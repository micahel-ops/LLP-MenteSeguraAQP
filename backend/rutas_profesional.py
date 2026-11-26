from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text

import reglas
from casos import BASE_ALERTAS, ORDEN, formatear, resumen_estados
from db import engine, iso, registrar
from seguridad import requiere


from io import BytesIO
import os

from fastapi.responses import StreamingResponse

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle
)

router = APIRouter(prefix="/api")
solo_profesional = requiere("PROFESIONAL")
CERRADOS = ("ATENDIDA", "DESCARTADA")



@router.get("/profesional/estudiantes")
def listar_mis_estudiantes(q: str = "", facultad: str = "", token: dict = Depends(solo_profesional)):
    """Lista estudiantes de las facultades asignadas al profesional."""
    with engine.connect() as conn:
        mi = conn.execute(
            text("""
                SELECT id
                FROM profesional
                WHERE usuario_id = :u
            """),
            {"u": int(token["sub"])}
        ).mappings().first()

        if mi is None:
            raise HTTPException(404, "No se encontró tu perfil de profesional")

        sql = """
            SELECT
                s.id,
                s.codigo,
                s.ciclo,
                f.nombre AS facultad,
                u.nombres,
                u.apellidos,
                u.correo,
                (SELECT MAX(e.fecha)
                 FROM evaluacion e
                 WHERE e.estudiante_id = s.id) AS ultima_fecha,
                (SELECT e.nivel_riesgo
                 FROM evaluacion e
                 WHERE e.estudiante_id = s.id
                 ORDER BY e.fecha DESC, e.id DESC
                 LIMIT 1) AS ultima_nivel,
                COUNT(DISTINCT CASE WHEN a.estado = 'NUEVA' THEN a.id END) AS casos_nuevos,
                COUNT(DISTINCT CASE WHEN a.estado = 'EN_REVISION' THEN a.id END) AS casos_en_revision,
                COUNT(DISTINCT CASE WHEN a.estado IN ('ATENDIDA', 'DESCARTADA') THEN a.id END) AS casos_cerrados
            FROM estudiante s
            JOIN facultad f ON f.id = s.facultad_id
            JOIN usuario u ON u.id = s.usuario_id
            JOIN profesional_facultad pf ON pf.facultad_id = s.facultad_id
            LEFT JOIN alerta a ON a.evaluacion_id IN (
                SELECT e.id
                FROM evaluacion e
                WHERE e.estudiante_id = s.id
            )
            WHERE pf.profesional_id = :profesional_id
        """

        params = {"profesional_id": mi["id"]}

        if facultad:
            sql += " AND s.facultad_id = :facultad"
            params["facultad"] = facultad

        if q:
            sql += """
                AND (
                    u.nombres LIKE :q
                    OR u.apellidos LIKE :q
                    OR u.correo LIKE :q
                    OR s.codigo LIKE :q
                )
            """
            params["q"] = f"%{q}%"

        sql += """
            GROUP BY
                s.id, s.codigo, s.ciclo, f.nombre,
                u.nombres, u.apellidos, u.correo
            ORDER BY u.apellidos, u.nombres
        """

        filas = conn.execute(
            text(sql), params
        ).mappings().all()

        resultados = [dict(f) for f in filas]

        # Evaluaciones recientes
        for r in resultados:
            r["evaluaciones"] = [
                dict(e) for e in conn.execute(
                    text("""
                        SELECT
                            e.id,
                            e.fecha,
                            i.codigo AS instrumento,
                            e.puntaje_instrumento AS puntaje,
                            e.categoria_instrumento AS categoria,
                            e.nivel_riesgo AS nivel
                        FROM evaluacion e
                        JOIN instrumento i ON i.id = e.instrumento_id
                        WHERE e.estudiante_id = :e
                        ORDER BY e.fecha DESC, e.id DESC
                        LIMIT 5
                    """),
                    {"e": r["id"]}
                ).mappings().all()
            ]

            # Alertas recientes
            alertas = conn.execute(
                text("""
                    SELECT
                        a.id,
                        a.prioridad,
                        a.motivo,
                        a.estado,
                        a.evaluacion_id,
                        (
                            SELECT COUNT(*)
                            FROM seguimiento sg
                            WHERE sg.alerta_id = a.id
                        ) AS n_seguimientos
                    FROM alerta a
                    JOIN evaluacion e ON e.id = a.evaluacion_id
                    WHERE e.estudiante_id = :e
                    ORDER BY a.prioridad DESC
                    LIMIT 5
                """),
                {"e": r["id"]}
            ).mappings().all()

            r["alertas"] = []
            for alerta in alertas:
                alerta = dict(alerta)
                etapa = reglas.etapa_caso(
                    alerta["estado"],
                    int(alerta["n_seguimientos"] or 0)
                )
                alerta["etapa_nombre"] = reglas.ETAPAS[etapa]
                alerta.pop("n_seguimientos", None)
                r["alertas"].append(alerta)

            # Datos para reportes
            total_eval = conn.execute(
                text("""
                    SELECT COUNT(*)
                    FROM evaluacion
                    WHERE estudiante_id = :e
                """),
                {"e": r["id"]}
            ).scalar()

            r["reporte"] = {
                "estudiante_id": r["id"],
                "total_evaluaciones": total_eval or 0,
                "ultima_fecha": r["ultima_fecha"],
                "ultima_nivel": r["ultima_nivel"],
                "casos_nuevos": r["casos_nuevos"] or 0,
                "casos_en_revision": r["casos_en_revision"] or 0,
                "casos_cerrados": r["casos_cerrados"] or 0
            }

    return resultados



def _mi_id(conn, token):
    pid = conn.execute(text("SELECT id FROM profesional WHERE usuario_id = :u"), {"u": int(token["sub"])}).scalar()
    if pid is None:
        raise HTTPException(404, "No se encontró tu perfil de profesional")
    return pid


def _para_actuar(conn, token, alerta_id, permitir_cerrada=False):
    """Comprueba que la alerta existe y que puedes actuar sobre ella."""
    mi = _mi_id(conn, token)
    a = conn.execute(text("SELECT id, estado, profesional_id FROM alerta WHERE id = :a"), {"a": alerta_id}).mappings().first()
    if a is None:
        raise HTTPException(404, "Alerta no encontrada")
    if a["profesional_id"] not in (None, mi):
        raise HTTPException(403, "Este caso está asignado a otro profesional")
    if a["estado"] in CERRADOS and not permitir_cerrada:
        raise HTTPException(409, "El caso ya está cerrado")
    return mi, a


@router.get("/alertas")
def listar_alertas(filtro: str = "todos", token: dict = Depends(solo_profesional)):
    with engine.connect() as conn:
        mi = _mi_id(conn, token)
        filas = conn.execute(text(BASE_ALERTAS + ORDEN)).mappings().all()
    todos = [formatear(f, mi) for f in filas]
    if filtro == "mios":
        casos = [c for c in todos if c["es_mio"]]
    elif filtro == "sin_asignar":
        casos = [c for c in todos if c["profesional_id"] is None]
    else:
        casos = todos
    return {
        "resumen": resumen_estados(casos),
        "contadores": {"todos": len(todos), "mios": sum(c["es_mio"] for c in todos),
                       "sin_asignar": sum(c["profesional_id"] is None for c in todos)},
        "alertas": casos,
    }


@router.get("/alertas/{alerta_id}")
def detalle_alerta(alerta_id: int, token: dict = Depends(solo_profesional)):
    with engine.connect() as conn:
        mi = _mi_id(conn, token)
        a = conn.execute(
            text("""SELECT a.id, a.prioridad, a.motivo, a.estado, a.creada_en, a.evaluacion_id, a.profesional_id,
                           e.fecha, e.nivel_riesgo, e.puntaje_instrumento AS puntaje, e.categoria_instrumento AS categoria,
                           e.puntaje_nlp, e.variacion_riesgo,
                           i.codigo AS instrumento, i.nombre AS instrumento_nombre,
                           s.id AS estudiante_id, s.codigo AS estudiante, s.ciclo, f.nombre AS facultad,
                           u.nombres, u.apellidos, u.correo,
                           up.nombres AS prof_nombres, up.apellidos AS prof_apellidos
                    FROM alerta a
                    JOIN evaluacion e ON e.id = a.evaluacion_id
                    JOIN instrumento i ON i.id = e.instrumento_id
                    JOIN estudiante s ON s.id = e.estudiante_id
                    JOIN facultad f ON f.id = s.facultad_id
                    JOIN usuario u ON u.id = s.usuario_id
                    LEFT JOIN profesional pr ON pr.id = a.profesional_id
                    LEFT JOIN usuario up ON up.id = pr.usuario_id
                    WHERE a.id = :a"""), {"a": alerta_id}).mappings().first()
        if a is None:
            raise HTTPException(404, "Alerta no encontrada")
        respuestas = conn.execute(
            text("""SELECT p.numero, p.enunciado, p.tipo, o.texto AS opcion, r.valor_numerico AS puntaje, r.texto_libre
                    FROM respuesta r JOIN pregunta p ON p.id = r.pregunta_id
                    LEFT JOIN opcion_respuesta o ON o.id = r.opcion_id
                    WHERE r.evaluacion_id = :e ORDER BY p.numero"""), {"e": a["evaluacion_id"]}).mappings().all()
        analisis = []
        for an in conn.execute(
                text("""SELECT an.id, an.nivel_riesgo, an.probabilidad, mv.version
                        FROM analisis_nlp an JOIN respuesta r ON r.id = an.respuesta_id
                        JOIN modelo_nlp_version mv ON mv.id = an.modelo_id WHERE r.evaluacion_id = :e"""),
                {"e": a["evaluacion_id"]}).mappings().all():
            terminos = conn.execute(
                text("SELECT termino, peso FROM termino_influyente WHERE analisis_id = :a ORDER BY ABS(peso) DESC"),
                {"a": an["id"]}).mappings().all()
            analisis.append({"nivel": an["nivel_riesgo"], "probabilidad": float(an["probabilidad"]), "modelo": an["version"],
                             "terminos": [{"termino": t["termino"], "peso": float(t["peso"])} for t in terminos]})
        seguimientos = conn.execute(
            text("""SELECT sg.fecha, sg.descripcion, sg.estado_resultante, up.nombres, up.apellidos
                    FROM seguimiento sg JOIN profesional pr ON pr.id = sg.profesional_id
                    JOIN usuario up ON up.id = pr.usuario_id WHERE sg.alerta_id = :a ORDER BY sg.fecha DESC, sg.id DESC"""),
            {"a": alerta_id}).mappings().all()
        validacion = conn.execute(
            text("SELECT confirma_riesgo, justificacion, fecha FROM validacion_alerta WHERE alerta_id = :a"),
            {"a": alerta_id}).mappings().first()
        historial = conn.execute(
            text("""SELECT e.id, e.fecha, i.codigo AS instrumento, e.puntaje_instrumento AS puntaje,
                           e.categoria_instrumento AS categoria, e.nivel_riesgo AS nivel
                    FROM evaluacion e JOIN instrumento i ON i.id = e.instrumento_id
                    WHERE e.estudiante_id = :s ORDER BY e.fecha DESC, e.id DESC LIMIT 10"""),
            {"s": a["estudiante_id"]}).mappings().all()

    segs = []
    for s in seguimientos:
        tipo, texto = reglas.desempaquetar_seguimiento(s["descripcion"])
        segs.append({"fecha": iso(s["fecha"]), "tipo": tipo, "descripcion": texto,
                     "estado": s["estado_resultante"], "profesional": f"{s['nombres']} {s['apellidos']}"})
    etapa = reglas.etapa_caso(a["estado"], len(segs))
    return {
        "alerta": {
            "id": a["id"], "prioridad": float(a["prioridad"]), "motivo": a["motivo"], "estado": a["estado"],
            "creada_en": iso(a["creada_en"]), "fecha": iso(a["fecha"]), "nivel": a["nivel_riesgo"],
            "puntaje": a["puntaje"], "categoria": a["categoria"], "variacion": a["variacion_riesgo"],
            "instrumento": a["instrumento"], "instrumento_nombre": a["instrumento_nombre"],
            "estudiante": a["estudiante"], "ciclo": a["ciclo"], "facultad": a["facultad"],
            "nombres": a["nombres"], "apellidos": a["apellidos"], "correo": a["correo"],
            "etapa": etapa, "etapa_nombre": reglas.ETAPAS[etapa],
            "asignado_a": None if a["profesional_id"] is None else f"{a['prof_nombres']} {a['prof_apellidos']}",
            "es_mio": a["profesional_id"] == mi, "sin_asignar": a["profesional_id"] is None,
            "puede_actuar": a["profesional_id"] in (None, mi),
        },
        "respuestas": [dict(r) for r in respuestas],
        "analisis": analisis,
        "seguimientos": segs,
        "validacion": None if validacion is None else {
            "confirma_riesgo": bool(validacion["confirma_riesgo"]), "justificacion": validacion["justificacion"],
            "fecha": iso(validacion["fecha"])},
        "historial": [{**dict(h), "fecha": iso(h["fecha"])} for h in historial],
    }


@router.post("/alertas/{alerta_id}/tomar")
def tomar_caso(alerta_id: int, token: dict = Depends(solo_profesional)):
    with engine.begin() as conn:
        mi = _mi_id(conn, token)
        a = conn.execute(text("SELECT id, profesional_id FROM alerta WHERE id = :a"), {"a": alerta_id}).mappings().first()
        if a is None:
            raise HTTPException(404, "Alerta no encontrada")
        if a["profesional_id"] not in (None, mi):
            raise HTTPException(409, "Este caso ya está asignado a otro profesional")
        conn.execute(text("UPDATE alerta SET profesional_id = :p, actualizada_en = :f WHERE id = :a"),
                     {"p": mi, "f": datetime.now(), "a": alerta_id})
        registrar(conn, int(token["sub"]), "CASO_TOMADO", "alerta", alerta_id)
    return {"asignado": True}


@router.post("/alertas/{alerta_id}/revision")
def iniciar_revision(alerta_id: int, token: dict = Depends(solo_profesional)):
    ahora = datetime.now()
    with engine.begin() as conn:
        mi, a = _para_actuar(conn, token, alerta_id)
        conn.execute(
            text("""UPDATE alerta SET estado = 'EN_REVISION', profesional_id = COALESCE(profesional_id, :p),
                    actualizada_en = :f WHERE id = :a"""), {"p": mi, "f": ahora, "a": alerta_id})
        if a["estado"] == "NUEVA":
            registrar(conn, int(token["sub"]), "REVISION_INICIADA", "alerta", alerta_id)
    return {"estado": "EN_REVISION"}


class SeguimientoIn(BaseModel):
    tipo: str
    descripcion: str


class ValidacionIn(BaseModel):
    confirma_riesgo: bool
    justificacion: str


@router.post("/alertas/{alerta_id}/seguimiento", status_code=201)
def registrar_seguimiento(alerta_id: int, datos: SeguimientoIn, token: dict = Depends(solo_profesional)):
    if datos.tipo not in reglas.TIPOS_SEGUIMIENTO:
        raise HTTPException(422, "Tipo de seguimiento no válido")
    if not datos.descripcion.strip():
        raise HTTPException(422, "Escribe una observación")
    ahora = datetime.now()
    with engine.begin() as conn:
        mi, a = _para_actuar(conn, token, alerta_id, permitir_cerrada=True)
        if a["estado"] in CERRADOS and datos.tipo != "CONTROL":
            raise HTTPException(409, "El caso está cerrado: solo puedes registrar controles")
        nuevo = "EN_REVISION" if a["estado"] == "NUEVA" else a["estado"]
        conn.execute(
            text("""INSERT INTO seguimiento (alerta_id, profesional_id, fecha, descripcion, estado_resultante)
                    VALUES (:a, :p, :f, :d, :e)"""),
            {"a": alerta_id, "p": mi, "f": ahora, "d": reglas.empaquetar_seguimiento(datos.tipo, datos.descripcion), "e": nuevo})
        conn.execute(
            text("""UPDATE alerta SET estado = :e, profesional_id = COALESCE(profesional_id, :p), actualizada_en = :f
                    WHERE id = :a"""), {"e": nuevo, "p": mi, "f": ahora, "a": alerta_id})
        registrar(conn, int(token["sub"]), "SEGUIMIENTO_REGISTRADO", "alerta", alerta_id)
    return {"estado": nuevo}


@router.post("/alertas/{alerta_id}/validacion", status_code=201)
def validar_alerta(alerta_id: int, datos: ValidacionIn, token: dict = Depends(solo_profesional)):
    if not datos.justificacion.strip():
        raise HTTPException(422, "Escribe una justificación")
    ahora = datetime.now()
    nuevo = "ATENDIDA" if datos.confirma_riesgo else "DESCARTADA"
    with engine.begin() as conn:
        mi, a = _para_actuar(conn, token, alerta_id)
        if conn.execute(text("SELECT id FROM validacion_alerta WHERE alerta_id = :a"), {"a": alerta_id}).first():
            raise HTTPException(409, "Esta alerta ya fue validada")
        conn.execute(
            text("""INSERT INTO validacion_alerta (alerta_id, profesional_id, confirma_riesgo, justificacion,
                        apta_entrenamiento, fecha) VALUES (:a, :p, :c, :j, TRUE, :f)"""),
            {"a": alerta_id, "p": mi, "c": datos.confirma_riesgo, "j": datos.justificacion.strip(), "f": ahora})
        conn.execute(
            text("""UPDATE alerta SET estado = :e, profesional_id = COALESCE(profesional_id, :p), actualizada_en = :f
                    WHERE id = :a"""), {"e": nuevo, "p": mi, "f": ahora, "a": alerta_id})
        registrar(conn, int(token["sub"]), "ALERTA_VALIDADA", "alerta", alerta_id)
    return {"estado": nuevo}



@router.get("/reportes/facultad")
def reporte_facultad(token: dict = Depends(solo_profesional)):
    """Reportes estadísticos de las facultades asignadas al profesional."""
    with engine.connect() as conn:
        # Obtener las facultades asignadas al profesional
        mi = conn.execute(
            text("""
                SELECT id
                FROM profesional
                WHERE usuario_id = :u
            """),
            {"u": int(token["sub"])}
        ).mappings().first()

        if mi is None:
            raise HTTPException(404, "No se encontró tu perfil de profesional")

        facultades = conn.execute(
            text("""
                SELECT f.id, f.nombre
                FROM profesional_facultad pf
                JOIN facultad f ON f.id = pf.facultad_id
                WHERE pf.profesional_id = :p
            """),
            {"p": mi["id"]}
        ).mappings().all()

        if not facultades:
            raise HTTPException(404, "No tienes facultades asignadas")

        facultad_ids = [f["id"] for f in facultades]
        nombres_facultades = ", ".join(f["nombre"] for f in facultades)

        # Estadísticas generales
        estadisticas = conn.execute(
            text("""
                SELECT
                    COUNT(DISTINCT e.id) AS evaluaciones,
                    COUNT(DISTINCT CASE
                        WHEN a.estado IN ('ATENDIDA', 'DESCARTADA')
                        THEN a.id END) AS evaluaciones_cerradas,
                    COUNT(DISTINCT CASE
                        WHEN a.estado = 'NUEVA'
                        THEN a.id END) AS casos_nuevos,
                    COUNT(DISTINCT CASE
                        WHEN a.estado = 'EN_REVISION'
                        THEN a.id END) AS en_revision,
                    COUNT(DISTINCT CASE
                        WHEN a.estado IN ('ATENDIDA', 'DESCARTADA')
                        THEN a.id END) AS casos_resueltos,
                    AVG(e.puntaje_instrumento) AS puntaje_promedio,
                    COUNT(DISTINCT s.id) AS estudiantes_activos
                FROM estudiante s
                LEFT JOIN evaluacion e ON e.estudiante_id = s.id
                LEFT JOIN alerta a ON a.evaluacion_id = e.id
                WHERE s.facultad_id IN :facultades
            """).bindparams(),
            {"facultades": tuple(facultad_ids)}
        ).mappings().first()

        # Profesionales asignados a las mismas facultades
        por_profesional = conn.execute(
            text("""
                SELECT
                    up.nombres AS nombres,
                    up.apellidos AS apellidos,
                    COUNT(DISTINCT a.id) AS casos_asignados,
                    COUNT(DISTINCT CASE
                        WHEN a.estado = 'ATENDIDA'
                        THEN a.id END) AS casos_atendidos,
                    COUNT(DISTINCT CASE
                        WHEN a.estado = 'DESCARTADA'
                        THEN a.id END) AS casos_descartados
                FROM profesional p
                JOIN usuario up ON up.id = p.usuario_id
                JOIN profesional_facultad pf
                    ON pf.profesional_id = p.id
                LEFT JOIN alerta a ON a.profesional_id = p.id
                WHERE pf.facultad_id IN :facultades
                  AND up.activo = TRUE
                GROUP BY p.id, up.id, up.nombres, up.apellidos
                ORDER BY casos_asignados DESC
            """).bindparams(),
            {"facultades": tuple(facultad_ids)}
        ).mappings().all()

    # Calcular porcentaje de resolución
    evaluaciones = estadisticas["evaluaciones"] or 0
    cerradas = estadisticas["casos_resueltos"] or 0
    porcentaje = round(
        (cerradas / evaluaciones) * 100, 1
    ) if evaluaciones else 0

    return {
        "facultad": nombres_facultades,
        "total_evaluaciones": evaluaciones,
        "evaluaciones_cerradas": estadisticas["evaluaciones_cerradas"] or 0,
        "casos_nuevos": estadisticas["casos_nuevos"] or 0,
        "en_revision": estadisticas["en_revision"] or 0,
        "casos_resueltos": cerradas,
        "puntaje_promedio": float(estadisticas["puntaje_promedio"] or 0),
        "estudiantes_activos": estadisticas["estudiantes_activos"] or 0,
        "porcentaje_casos_resueltos": porcentaje,
        "por_profesional": [dict(p) for p in por_profesional]
    }

@router.get("/reportes/facultad/pdf")
def reporte_facultad_pdf(token: dict = Depends(solo_profesional)):
    """Genera un PDF estadístico de las facultades del profesional."""

    # Reutilizar los datos del reporte existente
    datos = reporte_facultad(token)

    buffer = BytesIO()

    documento = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm
    )

    estilos = getSampleStyleSheet()

    # Fuente compatible con caracteres en español
    ruta_normal = "C:/Windows/Fonts/arial.ttf"
    ruta_negrita = "C:/Windows/Fonts/arialbd.ttf"

    if os.path.exists(ruta_normal):
        if "ArialPDF" not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont("ArialPDF", ruta_normal))

        if os.path.exists(ruta_negrita):
            if "ArialPDF-Bold" not in pdfmetrics.getRegisteredFontNames():
                pdfmetrics.registerFont(TTFont("ArialPDF-Bold", ruta_negrita))

        fuente = "ArialPDF"
        fuente_negrita = (
            "ArialPDF-Bold"
            if os.path.exists(ruta_negrita)
            else "ArialPDF"
        )
    else:
        fuente = "Helvetica"
        fuente_negrita = "Helvetica-Bold"

    estilos.add(ParagraphStyle(
        name="TituloReporte",
        parent=estilos["Title"],
        fontName=fuente_negrita,
        fontSize=18,
        alignment=TA_CENTER,
        spaceAfter=12
    ))

    estilos.add(ParagraphStyle(
        name="TextoReporte",
        parent=estilos["Normal"],
        fontName=fuente,
        fontSize=9,
        leading=13
    ))

    elementos = []

    elementos.append(Paragraph(
        "REPORTE ESTADÍSTICO PROFESIONAL",
        estilos["TituloReporte"]
    ))

    elementos.append(Paragraph(
        f"<b>Facultad:</b> {datos['facultad']}",
        estilos["TextoReporte"]
    ))

    elementos.append(Paragraph(
        f"<b>Fecha de generación:</b> {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        estilos["TextoReporte"]
    ))

    elementos.append(Spacer(1, 20))

    elementos.append(Paragraph(
        "<b>1. Resumen general</b>",
        estilos["Heading2"]
    ))

    resumen = [
        ["Indicador", "Resultado"],
        ["Total de evaluaciones", str(datos["total_evaluaciones"])],
        ["Estudiantes activos", str(datos["estudiantes_activos"])],
        ["Evaluaciones cerradas", str(datos["evaluaciones_cerradas"])],
        ["Casos nuevos", str(datos["casos_nuevos"])],
        ["Casos en revisión", str(datos["en_revision"])],
        ["Casos resueltos", str(datos["casos_resueltos"])],
        ["Puntaje promedio", str(round(datos["puntaje_promedio"], 2))],
        ["Porcentaje de resolución", f"{datos['porcentaje_casos_resueltos']}%"]
    ]

    tabla_resumen = Table(
        resumen,
        colWidths=[10 * cm, 6 * cm]
    )

    tabla_resumen.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#263B59")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, -1), fuente),
        ("FONTNAME", (0, 0), (-1, 0), fuente_negrita),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("PADDING", (0, 0), (-1, -1), 7),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE")
    ]))

    elementos.append(tabla_resumen)
    elementos.append(Spacer(1, 20))

    elementos.append(Paragraph(
        "<b>2. Estadísticas por profesional</b>",
        estilos["Heading2"]
    ))

    profesionales = [[
        "Profesional",
        "Asignados",
        "Atendidos",
        "Descartados"
    ]]

    for profesional in datos["por_profesional"]:
        nombre = (
            f"{profesional['nombres']} "
            f"{profesional['apellidos']}"
        )

        profesionales.append([
            Paragraph(nombre, estilos["TextoReporte"]),
            str(profesional["casos_asignados"]),
            str(profesional["casos_atendidos"]),
            str(profesional["casos_descartados"])
        ])

    tabla_profesionales = Table(
        profesionales,
        colWidths=[8 * cm, 2.5 * cm, 2.5 * cm, 3 * cm],
        repeatRows=1
    )

    tabla_profesionales.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#263B59")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, -1), fuente),
        ("FONTNAME", (0, 0), (-1, 0), fuente_negrita),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("PADDING", (0, 0), (-1, -1), 6),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE")
    ]))

    elementos.append(tabla_profesionales)

    documento.build(elementos)

    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": "attachment; filename=reporte_profesional.pdf"
        }
    )