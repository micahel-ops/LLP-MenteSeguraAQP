from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text

import nlp
import reglas
from db import engine, iso, registrar
from seguridad import requiere, usuario_actual, hash_clave

router = APIRouter(prefix="/api")
solo_estudiante = requiere("ESTUDIANTE")


def asegurar_modelo(conn):
    """Devuelve el id del modelo vigente; crea la versión heurística si no hay ninguno."""
    vigente = conn.execute(text("SELECT id FROM modelo_nlp_version WHERE estado = 'VIGENTE'")).scalar()
    if vigente:
        return vigente
    existente = conn.execute(text("SELECT id FROM modelo_nlp_version WHERE version = 'heuristico-v1.0'")).scalar()
    if existente:
        conn.execute(text("UPDATE modelo_nlp_version SET estado = 'VIGENTE' WHERE id = :i"), {"i": existente})
        return existente
    return conn.execute(
        text("""INSERT INTO modelo_nlp_version (version, estado, publicado_en, motivo_decision)
                VALUES ('heuristico-v1.0', 'VIGENTE', :f, 'Motor heurístico local inicial')"""),
        {"f": datetime.now()},
    ).lastrowid


# ---------------------------------------------------------------- perfil
@router.get("/estudiante/resumen")
def resumen(token: dict = Depends(solo_estudiante)):
    with engine.connect() as conn:
        p = conn.execute(
            text("""SELECT s.id, s.codigo, s.ciclo, s.consentimiento_aceptado, f.nombre AS facultad,
                           u.nombres, u.apellidos
                    FROM estudiante s JOIN facultad f ON f.id = s.facultad_id JOIN usuario u ON u.id = s.usuario_id
                    WHERE s.usuario_id = :u"""),
            {"u": int(token["sub"])},
        ).mappings().first()
        if p is None:
            raise HTTPException(404, "No se encontró el perfil de estudiante")
        total = conn.execute(text("SELECT COUNT(*) FROM evaluacion WHERE estudiante_id = :e"), {"e": p["id"]}).scalar()
        ultima = conn.execute(
            text("""SELECT fecha, nivel_riesgo FROM evaluacion WHERE estudiante_id = :e
                    ORDER BY fecha DESC, id DESC LIMIT 1"""), {"e": p["id"]}).mappings().first()
        proxima = conn.execute(
            text("""SELECT MIN(fecha_programada) FROM reevaluacion
                    WHERE estudiante_id = :e AND estado = 'PENDIENTE'"""), {"e": p["id"]}).scalar()
    return {
        "perfil": {"nombres": p["nombres"], "apellidos": p["apellidos"], "codigo": p["codigo"],
                   "facultad": p["facultad"], "ciclo": p["ciclo"],
                   "consentimiento_aceptado": bool(p["consentimiento_aceptado"])},
        "total": int(total or 0),
        "ultima": None if ultima is None else {"fecha": iso(ultima["fecha"]), "nivel": ultima["nivel_riesgo"]},
        "proxima_reevaluacion": None if proxima is None else str(proxima)[:10],
    }


@router.post("/estudiante/consentimiento")
def aceptar_consentimiento(token: dict = Depends(solo_estudiante)):
    with engine.begin() as conn:
        conn.execute(
            text("""UPDATE estudiante SET consentimiento_aceptado = TRUE, fecha_consentimiento = :f
                    WHERE usuario_id = :u"""), {"f": datetime.now(), "u": int(token["sub"])})
        registrar(conn, int(token["sub"]), "CONSENTIMIENTO_ACEPTADO", "estudiante")
    return {"consentimiento_aceptado": True}


# ---------------------------------------------------------------- cuestionarios
@router.get("/instrumentos")
def listar_instrumentos(token: dict = Depends(usuario_actual)):
    with engine.connect() as conn:
        filas = conn.execute(
            text("""SELECT i.codigo, i.nombre, i.tipo,
                           (SELECT COUNT(*) FROM pregunta p WHERE p.instrumento_id = i.id) AS preguntas
                    FROM instrumento i WHERE i.activo = TRUE ORDER BY i.id""")).mappings().all()
    return [dict(f) for f in filas]


@router.get("/instrumentos/{codigo}")
def cuestionario(codigo: str, token: dict = Depends(usuario_actual)):
    with engine.connect() as conn:
        ins = conn.execute(
            text("SELECT id, codigo, nombre FROM instrumento WHERE codigo = :c AND activo = TRUE"),
            {"c": codigo.upper()}).mappings().first()
        if ins is None:
            raise HTTPException(404, "Instrumento no encontrado")
        preguntas = conn.execute(
            text("""SELECT id, numero, enunciado, tipo, obligatoria FROM pregunta
                    WHERE instrumento_id = :i ORDER BY numero"""), {"i": ins["id"]}).mappings().all()
        opciones = conn.execute(
            text("""SELECT o.id, o.pregunta_id, o.texto FROM opcion_respuesta o
                    JOIN pregunta p ON p.id = o.pregunta_id WHERE p.instrumento_id = :i ORDER BY o.orden"""),
            {"i": ins["id"]}).mappings().all()
    return {
        "instrumento": dict(ins),
        "preguntas": [
            {**dict(p), "obligatoria": bool(p["obligatoria"]),
             "opciones": [{"id": o["id"], "texto": o["texto"]} for o in opciones if o["pregunta_id"] == p["id"]]}
            for p in preguntas
        ],
    }


class RespuestaIn(BaseModel):
    pregunta_id: int
    opcion_id: Optional[int] = None
    texto_libre: Optional[str] = None


class EvaluacionIn(BaseModel):
    instrumento: str
    respuestas: List[RespuestaIn]


@router.post("/evaluaciones", status_code=201)
def crear_evaluacion(datos: EvaluacionIn, token: dict = Depends(solo_estudiante)):
    ahora = datetime.now()
    uid = int(token["sub"])
    with engine.begin() as conn:
        est = conn.execute(
            text("SELECT id, consentimiento_aceptado FROM estudiante WHERE usuario_id = :u"), {"u": uid}
        ).mappings().first()
        if est is None:
            raise HTTPException(404, "No se encontró el perfil de estudiante")
        if not est["consentimiento_aceptado"]:
            raise HTTPException(403, "Debes aceptar el consentimiento informado")
        ins = conn.execute(
            text("SELECT id, codigo FROM instrumento WHERE codigo = :c AND activo = TRUE"),
            {"c": datos.instrumento.upper()}).mappings().first()
        if ins is None:
            raise HTTPException(404, "Instrumento no encontrado")

        preguntas = {p["id"]: p for p in conn.execute(
            text("SELECT id, numero, tipo, obligatoria FROM pregunta WHERE instrumento_id = :i"),
            {"i": ins["id"]}).mappings().all()}
        opciones = {o["id"]: o for o in conn.execute(
            text("""SELECT o.id, o.pregunta_id, o.puntaje FROM opcion_respuesta o
                    JOIN pregunta p ON p.id = o.pregunta_id WHERE p.instrumento_id = :i"""),
            {"i": ins["id"]}).mappings().all()}
        recibidas = {r.pregunta_id: r for r in datos.respuestas}
        if any(pid not in preguntas for pid in recibidas):
            raise HTTPException(422, "Hay preguntas que no pertenecen a este cuestionario")
        for pid, p in preguntas.items():
            r = recibidas.get(pid)
            if p["tipo"] == "CERRADA":
                if r is None or r.opcion_id is None:
                    raise HTTPException(422, f"Falta responder la pregunta {p['numero']}")
                if r.opcion_id not in opciones or opciones[r.opcion_id]["pregunta_id"] != pid:
                    raise HTTPException(422, f"Opción no válida en la pregunta {p['numero']}")
            elif p["obligatoria"] and not (r and (r.texto_libre or "").strip()):
                raise HTTPException(422, "Escribe tu respuesta en la pregunta abierta")

        # 1. Puntaje del instrumento
        puntaje = sum(opciones[r.opcion_id]["puntaje"] for pid, r in recibidas.items()
                      if preguntas[pid]["tipo"] == "CERRADA")
        critica9 = False
        if ins["codigo"] == "PHQ9":
            for pid, p in preguntas.items():
                if p["numero"] == 9 and p["tipo"] == "CERRADA":
                    critica9 = opciones[recibidas[pid].opcion_id]["puntaje"] > 0
        cat = reglas.categoria(ins["codigo"], puntaje)
        nivel_ins = reglas.nivel_instrumento(puntaje, critica9)

        # 2. Análisis del texto libre (PLN local)
        analisis = {}
        for pid, r in recibidas.items():
            if preguntas[pid]["tipo"] == "ABIERTA" and (r.texto_libre or "").strip():
                analisis[pid] = nlp.analizar_texto(r.texto_libre)
        peor = max(analisis.values(), key=lambda a: (a["critica"], a["neto"]), default=None)
        nivel_nlp = peor["nivel"] if peor else "BAJO"
        critica_nlp = bool(peor and peor["critica"])
        p_nlp = peor["probabilidad"] if peor else 0.0

        # 3. Nivel final, prioridad y cambio frente a la evaluación anterior
        nivel = reglas.mayor(nivel_ins, nivel_nlp)
        critica = critica9 or critica_nlp
        prioridad = puntaje + round(p_nlp * 20) + (50 if critica else 0)
        anterior = conn.execute(
            text("""SELECT puntaje_instrumento FROM evaluacion WHERE estudiante_id = :e AND instrumento_id = :i
                    ORDER BY fecha DESC, id DESC LIMIT 1"""), {"e": est["id"], "i": ins["id"]}).scalar()
        variacion = None if anterior is None else puntaje - anterior
        sube = variacion is not None and variacion >= 5 and nivel in ("MEDIO", "ALTO")

        modelo_id = asegurar_modelo(conn)
        eid = conn.execute(
            text("""INSERT INTO evaluacion (estudiante_id, instrumento_id, modelo_id, fecha, puntaje_instrumento,
                        categoria_instrumento, puntaje_nlp, nivel_riesgo, prioridad, variacion_riesgo, estado)
                    VALUES (:e, :i, :m, :f, :p, :c, :pn, :n, :pr, :v, 'ANALIZADA')"""),
            {"e": est["id"], "i": ins["id"], "m": modelo_id, "f": ahora, "p": puntaje, "c": cat, "pn": p_nlp,
             "n": nivel, "pr": prioridad, "v": variacion},
        ).lastrowid

        # 4. Respuestas y resultados del análisis
        for pid, r in recibidas.items():
            texto = (r.texto_libre or "").strip() or None
            valor = opciones[r.opcion_id]["puntaje"] if r.opcion_id else None
            if r.opcion_id is None and texto is None:
                continue
            rid = conn.execute(
                text("""INSERT INTO respuesta (evaluacion_id, pregunta_id, opcion_id, valor_numerico, texto_libre)
                        VALUES (:e, :p, :o, :v, :t)"""),
                {"e": eid, "p": pid, "o": r.opcion_id, "v": valor, "t": texto}).lastrowid
            if pid in analisis:
                a = analisis[pid]
                aid = conn.execute(
                    text("""INSERT INTO analisis_nlp (respuesta_id, modelo_id, nivel_riesgo, probabilidad, creado_en)
                            VALUES (:r, :m, :n, :p, :f)"""),
                    {"r": rid, "m": modelo_id, "n": a["nivel"], "p": a["probabilidad"], "f": ahora}).lastrowid
                for t in a["terminos"]:
                    conn.execute(
                        text("INSERT INTO termino_influyente (analisis_id, termino, peso) VALUES (:a, :t, :p)"),
                        {"a": aid, "t": t["termino"][:80], "p": t["peso"]})

        # 5. Alerta si corresponde
        motivos = []
        if critica9:
            motivos.append("Respuesta positiva al ítem 9 del PHQ-9")
        if critica_nlp:
            motivos.append("Expresiones de riesgo en el texto libre")
        elif nivel_nlp == "ALTO":
            motivos.append("Señales intensas en el texto libre")
        if puntaje >= 15:
            motivos.append(f"{ins['codigo']}: {puntaje} puntos ({cat})")
        if sube:
            motivos.append(f"Aumento de {variacion} puntos frente a la evaluación anterior")
        genera_alerta = nivel == "ALTO" or sube
        if genera_alerta:
            conn.execute(
                text("INSERT INTO alerta (evaluacion_id, prioridad, motivo, creada_en, actualizada_en) VALUES (:e, :p, :m, :f, :f)"),
                {"e": eid, "p": prioridad, "m": "; ".join(motivos)[:200] or "Revisión sugerida", "f": ahora})
        if nivel == "MEDIO":
            conn.execute(
                text("""INSERT INTO reevaluacion (estudiante_id, evaluacion_origen_id, fecha_programada, estado, recordatorio_enviado)
                        VALUES (:e, :o, :d, 'PENDIENTE', FALSE)"""),
                {"e": est["id"], "o": eid, "d": (ahora + timedelta(days=14)).date()})
        registrar(conn, uid, "EVALUACION_ENVIADA", "evaluacion", eid)

    nivel_msg = "ALTO" if genera_alerta and nivel != "ALTO" else nivel
    return {
        "evaluacion_id": eid, "puntaje": puntaje, "categoria": cat, "nivel": nivel,
        "mensaje": reglas.MENSAJES[nivel_msg], "recomendaciones": reglas.RECOMENDACIONES[nivel_msg],
        "mostrar_ayuda": nivel == "ALTO" or genera_alerta,
        "alerta_generada": genera_alerta,
        "reevaluacion": (ahora + timedelta(days=14)).date().isoformat() if nivel == "MEDIO" else None,
    }


@router.get("/mis-evaluaciones")
def mis_evaluaciones(token: dict = Depends(solo_estudiante)):
    with engine.connect() as conn:
        filas = conn.execute(
            text("""SELECT e.id, e.fecha, i.codigo AS instrumento, e.puntaje_instrumento AS puntaje,
                           e.categoria_instrumento AS categoria, e.nivel_riesgo AS nivel, a.estado AS alerta_estado
                    FROM evaluacion e
                    JOIN estudiante s ON s.id = e.estudiante_id
                    JOIN instrumento i ON i.id = e.instrumento_id
                    LEFT JOIN alerta a ON a.evaluacion_id = e.id
                    WHERE s.usuario_id = :u ORDER BY e.fecha DESC, e.id DESC"""),
            {"u": int(token["sub"])}).mappings().all()
    return [{"id": f["id"], "fecha": iso(f["fecha"]), "instrumento": f["instrumento"], "puntaje": f["puntaje"],
             "categoria": f["categoria"], "nivel": f["nivel"],
             "seguimiento": reglas.estado_para_estudiante(f["alerta_estado"])} for f in filas]


# ---------------------------------------------------------------- perfil
class PerfilPatch(BaseModel):
    nombres: Optional[str] = None
    apellidos: Optional[str] = None
    contrasena: Optional[str] = None


@router.patch("/estudiante/perfil")
def actualizar_perfil(datos: PerfilPatch, token: dict = Depends(solo_estudiante)):
    uid = int(token["sub"])
    with engine.begin() as conn:
        # Obtener info del usuario
        u = conn.execute(
            text("""SELECT u.id, u.nombres, u.apellidos, u.correo, u.contrasena_hash
                    FROM usuario u WHERE u.id = :i"""), {"i": uid}).mappings().first()
        if u is None:
            raise HTTPException(404, "Usuario no encontrado")

        campos = {}
        if datos.nombres is not None:
            if not datos.nombres.strip():
                raise HTTPException(422, "Escribe los nombres")
            campos["nombres"] = datos.nombres.strip()
        if datos.apellidos is not None:
            if not datos.apellidos.strip():
                raise HTTPException(422, "Escribe los apellidos")
            campos["apellidos"] = datos.apellidos.strip()
        if datos.contrasena is not None:
            if len(datos.contrasena) < 8:
                raise HTTPException(422, "La contraseña debe tener al menos 8 caracteres")
            campos["contrasena_hash"] = hash_clave(datos.contrasena)
            campos["intentos_fallidos"] = 0
            campos["bloqueado_hasta"] = None

        if campos:
            sets = ", ".join(f"{k} = :{k}" for k in campos)
            conn.execute(text(f"UPDATE usuario SET {sets} WHERE id = :_id"), {**campos, "_id": uid})
            registrar(conn, uid, "PERFIL_EDITADO", "usuario", uid)

    return {"ok": True}
