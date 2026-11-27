
from datetime import datetime
from typing import Optional
import re
from io import BytesIO

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from fastapi.responses import StreamingResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

from db import engine, registrar
from casos import BASE_ALERTAS, ORDEN, formatear, resumen_estados
from seguridad import requiere, hash_clave

router = APIRouter(prefix="/api/admin")
solo_admin = requiere("ADMINISTRADOR")
class AsignacionCasoIn(BaseModel):
    profesional_id: Optional[int] = None

ROLES = ("ESTUDIANTE", "PROFESIONAL", "ADMINISTRADOR")
ESTADOS_MODELO = ("CANDIDATA", "VIGENTE", "RECHAZADA", "RETIRADA")
CORREO = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

ROL_POR_OPCION = {
    1: "ESTUDIANTE",
    2: "PROFESIONAL",
    3: "ADMINISTRADOR"
}


# ============================================================
# FUENTES EXTERNAS
# ============================================================

class FuenteExternaIn(BaseModel):
    nombre: str
    organismo_tipo: str
    tipo_acceso: str
    clasificacion: str
    url: str
    frecuencia_dias: int = 7
    activa: bool = True


class FuenteExternaPatch(BaseModel):
    nombre: Optional[str] = None
    organismo_tipo: Optional[str] = None
    tipo_acceso: Optional[str] = None
    clasificacion: Optional[str] = None
    url: Optional[str] = None
    frecuencia_dias: Optional[int] = None
    activa: Optional[bool] = None


@router.get("/fuentes-externas")
def listar_fuentes_externas(token: dict = Depends(solo_admin)):
    with engine.connect() as conn:
        filas = conn.execute(
            text("""
                SELECT
                    fe.id,
                    fe.nombre,
                    fe.organismo_tipo,
                    fe.tipo_acceso,
                    fe.clasificacion,
                    fe.url,
                    fe.frecuencia_dias,
                    fe.activa,
                    fe.ultima_actualizacion,
                    fe.creada_en,
                    COUNT(d.id) AS datos_asociados
                FROM fuente_externa fe
                LEFT JOIN dato_externo d
                    ON d.fuente_id = fe.id
                GROUP BY
                    fe.id,
                    fe.nombre,
                    fe.organismo_tipo,
                    fe.tipo_acceso,
                    fe.clasificacion,
                    fe.url,
                    fe.frecuencia_dias,
                    fe.activa,
                    fe.ultima_actualizacion,
                    fe.creada_en
                ORDER BY fe.nombre
            """)
        ).mappings().all()

    return [dict(f) for f in filas]


@router.post("/fuentes-externas", status_code=201)
def crear_fuente_externa(
    datos: FuenteExternaIn,
    token: dict = Depends(solo_admin)
):
    nombre = datos.nombre.strip()

    if len(nombre) < 3:
        raise HTTPException(422, "El nombre debe tener al menos 3 caracteres")

    if datos.frecuencia_dias < 1:
        raise HTTPException(422, "La frecuencia debe ser mayor que cero")

    with engine.begin() as conn:
        existe = conn.execute(
            text("""
                SELECT id
                FROM fuente_externa
                WHERE nombre = :n
            """),
            {"n": nombre}
        ).first()

        if existe:
            raise HTTPException(409, "Ya existe una fuente externa con ese nombre")

        resultado = conn.execute(
            text("""
                INSERT INTO fuente_externa (
                    nombre,
                    organismo_tipo,
                    tipo_acceso,
                    clasificacion,
                    url,
                    frecuencia_dias,
                    activa
                )
                VALUES (
                    :nombre,
                    :organismo_tipo,
                    :tipo_acceso,
                    :clasificacion,
                    :url,
                    :frecuencia_dias,
                    :activa
                )
            """),
            {
                "nombre": nombre,
                "organismo_tipo": datos.organismo_tipo.strip(),
                "tipo_acceso": datos.tipo_acceso.strip(),
                "clasificacion": datos.clasificacion.strip(),
                "url": datos.url.strip(),
                "frecuencia_dias": datos.frecuencia_dias,
                "activa": datos.activa
            }
        )

        fuente_id = resultado.lastrowid

        registrar(
            conn,
            int(token["sub"]),
            "FUENTE_EXTERNA_CREADA",
            "fuente_externa",
            fuente_id
        )

    return {
        "id": fuente_id,
        "nombre": nombre
    }


@router.patch("/fuentes-externas/{fuente_id}")
def editar_fuente_externa(
    fuente_id: int,
    datos: FuenteExternaPatch,
    token: dict = Depends(solo_admin)
):
    with engine.begin() as conn:
        fuente = conn.execute(
            text("SELECT id FROM fuente_externa WHERE id = :i"),
            {"i": fuente_id}
        ).first()

        if not fuente:
            raise HTTPException(404, "Fuente externa no encontrada")

        valores = datos.model_dump(exclude_unset=True)
        campos = {}

        for campo, valor in valores.items():
            if isinstance(valor, str):
                valor = valor.strip()

            campos[campo] = valor

        if "nombre" in campos:
            if len(campos["nombre"]) < 3:
                raise HTTPException(422, "El nombre debe tener al menos 3 caracteres")

            existe = conn.execute(
                text("""
                    SELECT id
                    FROM fuente_externa
                    WHERE nombre = :n AND id != :i
                """),
                {
                    "n": campos["nombre"],
                    "i": fuente_id
                }
            ).first()

            if existe:
                raise HTTPException(409, "Ya existe una fuente externa con ese nombre")

        if "frecuencia_dias" in campos and campos["frecuencia_dias"] < 1:
            raise HTTPException(422, "La frecuencia debe ser mayor que cero")

        if campos:
            sets = ", ".join(
                f"{campo} = :{campo}" for campo in campos
            )

            conn.execute(
                text(f"""
                    UPDATE fuente_externa
                    SET {sets}
                    WHERE id = :_id
                """),
                {
                    **campos,
                    "_id": fuente_id
                }
            )

            registrar(
                conn,
                int(token["sub"]),
                "FUENTE_EXTERNA_EDITADA",
                "fuente_externa",
                fuente_id
            )

    return {"ok": True}


@router.delete("/fuentes-externas/{fuente_id}", status_code=204)
def eliminar_fuente_externa(
    fuente_id: int,
    token: dict = Depends(solo_admin)
):
    with engine.begin() as conn:
        fuente = conn.execute(
            text("SELECT id FROM fuente_externa WHERE id = :i"),
            {"i": fuente_id}
        ).first()

        if not fuente:
            raise HTTPException(404, "Fuente externa no encontrada")

        datos_asociados = conn.execute(
            text("""
                SELECT COUNT(*)
                FROM dato_externo
                WHERE fuente_id = :f
            """),
            {"f": fuente_id}
        ).scalar()

        if datos_asociados > 0:
            raise HTTPException(
                409,
                "No se puede eliminar: hay datos externos asociados a esta fuente"
            )

        conn.execute(
            text("DELETE FROM fuente_externa WHERE id = :i"),
            {"i": fuente_id}
        )

        registrar(
            conn,
            int(token["sub"]),
            "FUENTE_EXTERNA_ELIMINADA",
            "fuente_externa",
            fuente_id
        )


# ============================================================
# MODELOS NLP
# ============================================================

class ModeloNLPIn(BaseModel):
    version: str
    estado: str = "VIGENTE"
    publicado_en: Optional[datetime] = None
    motivo_decision: Optional[str] = None


class ModeloNLPPatch(BaseModel):
    version: Optional[str] = None
    estado: Optional[str] = None
    motivo_decision: Optional[str] = None


@router.get("/modelo-nlp")
def listar_modelos_nlp(token: dict = Depends(solo_admin)):
    with engine.connect() as conn:
        filas = conn.execute(
            text("""
                SELECT
                    id,
                    version,
                    estado,
                    publicado_en,
                    motivo_decision,
                    creado_en,
                    vigente
                FROM modelo_nlp_version
                ORDER BY publicado_en DESC
            """)
        ).mappings().all()

    return [dict(f) for f in filas]


@router.post("/modelo-nlp", status_code=201)
def crear_modelo_nlp(
    datos: ModeloNLPIn,
    token: dict = Depends(solo_admin)
):
    version = datos.version.strip()
    estado = datos.estado.strip().upper()

    if not version:
        raise HTTPException(422, "La versión es obligatoria")

    if estado not in ESTADOS_MODELO:
        raise HTTPException(422, "Estado de modelo NLP no válido")

    with engine.begin() as conn:
        existe = conn.execute(
            text("""
                SELECT id
                FROM modelo_nlp_version
                WHERE version = :v
            """),
            {"v": version}
        ).first()

        if existe:
            raise HTTPException(
                409,
                f"Ya existe un modelo NLP con la versión '{version}'"
            )

        if estado == "VIGENTE":
            conn.execute(
                text("""
                    UPDATE modelo_nlp_version
                    SET estado = 'RETIRADA'
                    WHERE estado = 'VIGENTE'
                """)
            )

        modelo_id = conn.execute(
            text("""
                INSERT INTO modelo_nlp_version (
                    version,
                    estado,
                    publicado_en,
                    motivo_decision
                )
                VALUES (:v, :e, :p, :m)
            """),
            {
                "v": version,
                "e": estado,
                "p": datos.publicado_en or (
                    datetime.now() if estado == "VIGENTE" else None
                ),
                "m": (
                    datos.motivo_decision.strip()
                    if datos.motivo_decision
                    else None
                )
            }
        ).lastrowid

        registrar(
            conn,
            int(token["sub"]),
            "MODELO_NLP_CREADO",
            "modelo_nlp_version",
            modelo_id
        )

    return {
        "id": modelo_id,
        "version": version,
        "estado": estado
    }


@router.patch("/modelo-nlp/{modelo_id}")
def editar_modelo_nlp(
    modelo_id: int,
    datos: ModeloNLPPatch,
    token: dict = Depends(solo_admin)
):
    with engine.begin() as conn:
        modelo = conn.execute(
            text("""
                SELECT id, version, estado
                FROM modelo_nlp_version
                WHERE id = :i
            """),
            {"i": modelo_id}
        ).mappings().first()

        if modelo is None:
            raise HTTPException(404, "Modelo NLP no encontrado")

        estado_nuevo = (
            datos.estado.strip().upper()
            if datos.estado is not None
            else modelo["estado"]
        )

        if estado_nuevo not in ESTADOS_MODELO:
            raise HTTPException(422, "Estado de modelo NLP no válido")

        campos = {}

        if datos.version is not None:
            version = datos.version.strip()

            if not version:
                raise HTTPException(422, "La versión es obligatoria")

            existe = conn.execute(
                text("""
                    SELECT id
                    FROM modelo_nlp_version
                    WHERE version = :v AND id != :i
                """),
                {
                    "v": version,
                    "i": modelo_id
                }
            ).first()

            if existe:
                raise HTTPException(
                    409,
                    f"Ya existe un modelo NLP con la versión '{version}'"
                )

            campos["version"] = version

        if datos.estado is not None:
            campos["estado"] = estado_nuevo

        if datos.motivo_decision is not None:
            campos["motivo_decision"] = (
                datos.motivo_decision.strip()
                if datos.motivo_decision
                else None
            )

        if estado_nuevo == "VIGENTE" and modelo["estado"] != "VIGENTE":
            conn.execute(
                text("""
                    UPDATE modelo_nlp_version
                    SET estado = 'RETIRADA'
                    WHERE estado = 'VIGENTE'
                      AND id != :i
                """),
                {"i": modelo_id}
            )

        if campos:
            sets = ", ".join(
                f"{campo} = :{campo}" for campo in campos
            )

            conn.execute(
                text(f"""
                    UPDATE modelo_nlp_version
                    SET {sets}
                    WHERE id = :_id
                """),
                {
                    **campos,
                    "_id": modelo_id
                }
            )

            registrar(
                conn,
                int(token["sub"]),
                "MODELO_NLP_EDITADO",
                "modelo_nlp_version",
                modelo_id
            )

    return {"ok": True}


@router.delete("/modelo-nlp/{modelo_id}", status_code=204)
def eliminar_modelo_nlp(
    modelo_id: int,
    token: dict = Depends(solo_admin)
):
    with engine.begin() as conn:
        modelo = conn.execute(
            text("SELECT id FROM modelo_nlp_version WHERE id = :i"),
            {"i": modelo_id}
        ).first()

        if not modelo:
            raise HTTPException(404, "Modelo NLP no encontrado")

        evaluaciones = conn.execute(
            text("""
                SELECT COUNT(*)
                FROM evaluacion
                WHERE modelo_id = :m
            """),
            {"m": modelo_id}
        ).scalar()

        if evaluaciones > 0:
            raise HTTPException(
                409,
                "No se puede eliminar: hay evaluaciones asociadas a este modelo"
            )

        conn.execute(
            text("DELETE FROM modelo_nlp_version WHERE id = :i"),
            {"i": modelo_id}
        )

        registrar(
            conn,
            int(token["sub"]),
            "MODELO_NLP_ELIMINADO",
            "modelo_nlp_version",
            modelo_id
        )


# ============================================================
# REPORTES PROFESIONALES
# ============================================================

@router.get("/reportes/profesionales")
def listar_reportes_profesionales(
    token: dict = Depends(solo_admin)
):
    with engine.connect() as conn:
        filas = conn.execute(
            text("""
                SELECT
                    f.id AS facultad_id,
                    f.nombre AS facultad,
                    COUNT(DISTINCT e.id) AS evaluaciones,
                    COUNT(DISTINCT a.id) AS total_alertas,
                    COUNT(DISTINCT CASE
                        WHEN a.estado IN ('ATENDIDA', 'DESCARTADA')
                        THEN a.id
                    END) AS evaluaciones_cerradas,
                    COUNT(DISTINCT CASE
                        WHEN a.estado = 'NUEVA'
                        THEN a.id
                    END) AS casos_nuevos,
                    COUNT(DISTINCT CASE
                        WHEN a.estado = 'EN_REVISION'
                        THEN a.id
                    END) AS en_revision,
                    COUNT(DISTINCT CASE
                        WHEN a.estado IN ('ATENDIDA', 'DESCARTADA')
                        THEN a.id
                    END) AS casos_resueltos,
                    AVG(e.puntaje_instrumento) AS puntaje_promedio,
                    COUNT(DISTINCT s.id) AS estudiantes_activos
                FROM facultad f
                LEFT JOIN estudiante s
                    ON s.facultad_id = f.id
                LEFT JOIN evaluacion e
                    ON e.estudiante_id = s.id
                LEFT JOIN alerta a
                    ON a.evaluacion_id = e.id
                GROUP BY f.id, f.nombre
                ORDER BY f.nombre
            """)
        ).mappings().all()

        tendencias_filas = conn.execute(
            text("""
                SELECT
                    s.facultad_id,
                    DATE_FORMAT(e.fecha, '%Y-%m') AS mes,
                    COUNT(DISTINCT e.id) AS evaluaciones,
                    COUNT(DISTINCT CASE
                        WHEN a.estado = 'NUEVA'
                        THEN a.id
                    END) AS casos_nuevos,
                    AVG(e.puntaje_instrumento) AS puntaje_promedio
                FROM evaluacion e
                JOIN estudiante s
                    ON s.id = e.estudiante_id
                LEFT JOIN alerta a
                    ON a.evaluacion_id = e.id
                WHERE e.fecha >= DATE_SUB(
                    CURRENT_DATE(),
                    INTERVAL 5 MONTH
                )
                GROUP BY
                    s.facultad_id,
                    DATE_FORMAT(e.fecha, '%Y-%m')
                ORDER BY mes
            """)
        ).mappings().all()

    tendencias_por_facultad = {}

    for fila in tendencias_filas:
        facultad_id = fila["facultad_id"]

        if facultad_id not in tendencias_por_facultad:
            tendencias_por_facultad[facultad_id] = {}

        tendencias_por_facultad[facultad_id][fila["mes"]] = {
            "evaluaciones": fila["evaluaciones"] or 0,
            "casos_nuevos": fila["casos_nuevos"] or 0,
            "puntaje_promedio": float(fila["puntaje_promedio"] or 0)
        }

    reportes = []

    for fila in filas:
        total_alertas = fila["total_alertas"] or 0
        casos_resueltos = fila["casos_resueltos"] or 0

        porcentaje = (
            round((casos_resueltos / total_alertas) * 100, 1)
            if total_alertas > 0
            else 0
        )

        reportes.append({
            "facultad": fila["facultad"],
            "total_evaluaciones": fila["evaluaciones"] or 0,
            "total_alertas": total_alertas,
            "evaluaciones_cerradas": fila["evaluaciones_cerradas"] or 0,
            "casos_nuevos": fila["casos_nuevos"] or 0,
            "en_revision": fila["en_revision"] or 0,
            "casos_resueltos": casos_resueltos,
            "puntaje_promedio": float(fila["puntaje_promedio"] or 0),
            "estudiantes_activos": fila["estudiantes_activos"] or 0,
            "porcentaje_casos_resueltos": porcentaje,
            "tendencias": tendencias_por_facultad.get(
                fila["facultad_id"], {}
            )
        })

    return {
        "reportes": reportes,
        "total_facultades": len(reportes),
        "total_evaluaciones": sum(
            r["total_evaluaciones"] for r in reportes
        ),
        "total_estudiantes": sum(
            r["estudiantes_activos"] for r in reportes
        )
    }


# ============================================================
# PANEL GENERAL
# ============================================================

@router.get("/panel")
def panel_general(token: dict = Depends(solo_admin)):
    with engine.connect() as conn:

        # Usuarios por rol
        usuarios_query = conn.execute(
            text("""
                SELECT
                    u.rol_id,
                    r.nombre AS rol_nombre,
                    COUNT(*) AS total,
                    COUNT(
                        CASE WHEN u.activo = TRUE THEN 1 END
                    ) AS activos
                FROM usuario u
                JOIN rol r
                    ON r.id = u.rol_id
                GROUP BY u.rol_id, r.nombre
                ORDER BY r.nombre
            """)
        ).mappings().all()

        usuarios = [
            {
                "rol": u["rol_id"],
                "nombre": u["rol_nombre"],
                "activos": u["activos"],
                "total": u["total"]
            }
            for u in usuarios_query
        ]

        # Alertas por estado
        alertas_query = conn.execute(
            text("""
                SELECT
                    estado,
                    COUNT(*) AS total
                FROM alerta
                GROUP BY estado
                ORDER BY FIELD(
                    estado,
                    'NUEVA',
                    'EN_REVISION',
                    'ATENDIDA',
                    'DESCARTADA'
                )
            """)
        ).mappings().all()

        alertas = {
            row["estado"]: row["total"]
            for row in alertas_query
        }

        alertas_estado = {
            "nuevas": alertas.get("NUEVA", 0),
            "en_revision": alertas.get("EN_REVISION", 0),
            "sin_asignar": 0,
            "por_etapa": 0,
            "atendidas": alertas.get("ATENDIDA", 0),
            "descartadas": alertas.get("DESCARTADA", 0)
        }

        # Evaluaciones por nivel de riesgo y mes
        evaluaciones_query = conn.execute(
            text("""
                SELECT
                    e.nivel_riesgo,
                    COUNT(*) AS total,
                    MONTH(e.fecha) AS mes,
                    YEAR(e.fecha) AS anio
                FROM evaluacion e
                GROUP BY
                    e.nivel_riesgo,
                    YEAR(e.fecha),
                    MONTH(e.fecha)
                ORDER BY anio DESC, mes DESC
            """)
        ).mappings().all()

        niveles_existentes = conn.execute(
            text("""
                SELECT DISTINCT nivel_riesgo
                FROM evaluacion
            """)
        ).mappings().all()

        por_nivel = {
            row["nivel_riesgo"]: 0
            for row in niveles_existentes
        }

        por_mes = {}

        for row in evaluaciones_query:
            nivel = row["nivel_riesgo"]

            por_nivel[nivel] = (
                por_nivel.get(nivel, 0) + row["total"]
            )

            mes_anio = f"{row['anio']}-{row['mes']:02d}"

            por_mes[mes_anio] = (
                por_mes.get(mes_anio, 0) + row["total"]
            )

        meses_ordenados = sorted(
            por_mes.keys(),
            reverse=True
        )[:6]

        por_mes_ordenados = [
            {
                "mes": mes,
                "total": por_mes[mes]
            }
            for mes in meses_ordenados
        ]

        # Facultades
        facultades_query = conn.execute(
            text("""
                SELECT
                    f.id,
                    f.nombre,
                    COUNT(DISTINCT e.id) AS evaluaciones,
                    COUNT(DISTINCT a.id) AS alertas
                FROM facultad f
                LEFT JOIN estudiante s
                    ON s.facultad_id = f.id
                LEFT JOIN evaluacion e
                    ON e.estudiante_id = s.id
                LEFT JOIN alerta a
                    ON a.evaluacion_id = e.id
                GROUP BY f.id, f.nombre
                ORDER BY f.nombre
            """)
        ).mappings().all()

        facultades = [
            dict(f)
            for f in facultades_query
        ]

    return {
        "usuarios": usuarios,
        "alertas": alertas_estado,
        "evaluaciones": {
            "total": sum(por_nivel.values()),
            "por_nivel": por_nivel,
            "por_mes": por_mes_ordenados
        },
        "facultades": facultades
    }


# ============================================================
# CASOS
# ============================================================

@router.get("/casos")
def listar_casos(token: dict = Depends(solo_admin)):
    with engine.connect() as conn:
        filas = conn.execute(
            text(BASE_ALERTAS + ORDEN)
        ).mappings().all()

        profesionales = conn.execute(
            text("""
                SELECT
                    p.id,
                    CONCAT(u.nombres, ' ', u.apellidos) AS nombre
                FROM profesional p
                JOIN usuario u
                    ON u.id = p.usuario_id
                WHERE u.activo = TRUE
                ORDER BY u.apellidos, u.nombres
            """)
        ).mappings().all()

    casos = [formatear(f) for f in filas]

    return {
        "resumen": resumen_estados(casos),
        "casos": casos,
        "profesionales": [dict(p) for p in profesionales]
    }


@router.post("/casos/{alerta_id}/asignar")
def asignar_caso(
    alerta_id: int,
    datos: AsignacionCasoIn,
    token: dict = Depends(solo_admin)
):
    with engine.begin() as conn:

        caso = conn.execute(
            text("""
                SELECT id, estado
                FROM alerta
                WHERE id = :id
            """),
            {"id": alerta_id}
        ).mappings().first()

        if not caso:
            raise HTTPException(
                status_code=404,
                detail="El caso no existe."
            )

        if caso["estado"] in ("ATENDIDA", "DESCARTADA"):
            raise HTTPException(
                status_code=409,
                detail="No se puede modificar la asignación de un caso cerrado."
            )

        if datos.profesional_id is not None:
            profesional = conn.execute(
                text("""
                    SELECT p.id
                    FROM profesional p
                    JOIN usuario u
                        ON u.id = p.usuario_id
                    WHERE p.id = :id
                    AND u.activo = TRUE
                """),
                {"id": datos.profesional_id}
            ).scalar()

            if profesional is None:
                raise HTTPException(
                    status_code=404,
                    detail="El profesional no existe o está inactivo."
                )

        conn.execute(
            text("""
                UPDATE alerta
                SET profesional_id = :profesional_id,
                    actualizada_en = :actualizada_en
                WHERE id = :id
            """),
            {
                "profesional_id": datos.profesional_id,
                "actualizada_en": datetime.now(),
                "id": alerta_id
            }
        )

    return {
        "mensaje": "Asignación actualizada correctamente."
    }


# ============================================================
# ACTIVIDAD
# ============================================================

@router.get("/actividad")
def listar_actividad(token: dict = Depends(solo_admin)):
    with engine.connect() as conn:
        actividad = conn.execute(
            text("""
                SELECT
                    ra.*,
                    u.nombres,
                    u.apellidos,
                    u.correo
                FROM registro_actividad ra
                LEFT JOIN usuario u
                    ON u.id = ra.usuario_id
                ORDER BY ra.fecha DESC
            """)
        ).mappings().all()

    return [dict(a) for a in actividad]


# ============================================================
# USUARIOS
# ============================================================


@router.get("/usuarios")
def listar_usuarios(
    rol: str = "",
    q: str = "",
    token: dict = Depends(solo_admin)
):
    with engine.connect() as conn:
        consulta = """
            SELECT
                u.id,
                u.rol_id,
                u.correo,
                u.nombres,
                u.apellidos,
                u.activo,
                u.ultimo_acceso,
                u.creado_en,
                r.nombre AS rol,
                e.id AS estudiante_id,
                e.facultad_id,
                e.codigo,
                e.ciclo,
                p.id AS profesional_id,
                p.especialidad,
                p.numero_colegiatura
            FROM usuario u
            JOIN rol r ON r.id = u.rol_id
            LEFT JOIN estudiante e ON e.usuario_id = u.id
            LEFT JOIN profesional p ON p.usuario_id = u.id
            WHERE 1=1
        """

        parametros = {}

        if rol:
            consulta += " AND r.nombre = :rol"
            parametros["rol"] = rol

        if q:
            consulta += """
                AND (
                    u.nombres LIKE :q
                    OR u.apellidos LIKE :q
                    OR u.correo LIKE :q
                )
            """
            parametros["q"] = f"%{q}%"

        consulta += " ORDER BY u.creado_en DESC"

        usuarios = conn.execute(
            text(consulta), parametros
        ).mappings().all()

        resultado = []

        for usuario in usuarios:
            u = dict(usuario)

            profesional_id = u.pop("profesional_id", None)
            estudiante_id = u.pop("estudiante_id", None)

            u["bloqueado"] = False
            u["facultades"] = []

            if profesional_id:
                facultades = conn.execute(
                    text("""
                        SELECT f.id, f.nombre
                        FROM profesional_facultad pf
                        JOIN facultad f ON f.id = pf.facultad_id
                        WHERE pf.profesional_id = :id
                    """),
                    {"id": profesional_id}
                ).mappings().all()

                u["facultades"] = [dict(f) for f in facultades]

            resultado.append(u)

    return resultado

class UsuarioCrearIn(BaseModel):
    correo: str
    contrasena: str
    nombres: str
    apellidos: str
    rol_id: int
    facultad_id: Optional[int] = None
    ciclo: Optional[int] = None
    codigo: Optional[str] = None
    especialidad: Optional[str] = None
    numero_colegiatura: Optional[str] = None
    facultades: Optional[list[int]] = None

class UsuarioPatchIn(BaseModel):
    nombres: Optional[str] = None
    apellidos: Optional[str] = None
    contrasena: Optional[str] = None
    activo: Optional[bool] = None
    desbloquear: Optional[bool] = None
    facultad_id: Optional[int] = None
    ciclo: Optional[int] = None
    especialidad: Optional[str] = None
    numero_colegiatura: Optional[str] = None
    facultades: Optional[list[int]] = None


@router.post("/usuarios", status_code=201)
def crear_usuario(
    datos: UsuarioCrearIn,
    token: dict = Depends(solo_admin)
):
    correo = datos.correo.strip().lower()
    nombres = datos.nombres.strip()
    apellidos = datos.apellidos.strip()

    if not CORREO.match(correo):
        raise HTTPException(422, "Correo no válido.")

    if len(datos.contrasena) < 8:
        raise HTTPException(422, "La contraseña debe tener al menos 8 caracteres.")

    if not nombres or not apellidos:
        raise HTTPException(422, "Nombres y apellidos son obligatorios.")

    nombre_rol = ROL_POR_OPCION.get(datos.rol_id)
    if nombre_rol is None:
        raise HTTPException(422, "Rol no válido.")

    with engine.begin() as conn:
        rol_id_db = conn.execute(
            text("SELECT id FROM rol WHERE nombre = :nombre"),
            {"nombre": nombre_rol}
        ).scalar()
        if rol_id_db is None:
            raise HTTPException(409, "No está configurado el rol solicitado. Inicializa los datos base.")

        existe = conn.execute(
            text("SELECT id FROM usuario WHERE correo = :correo"),
            {"correo": correo}
        ).first()

        if existe:
            raise HTTPException(409, "El correo ya está registrado.")

        if nombre_rol == "ESTUDIANTE":
            if not datos.facultad_id:
                raise HTTPException(422, "Selecciona una facultad.")

            facultad = conn.execute(
                text("SELECT id FROM facultad WHERE id = :id"),
                {"id": datos.facultad_id}
            ).first()

            if not facultad:
                raise HTTPException(404, "Facultad no encontrada.")

            if datos.ciclo is not None and not 1 <= datos.ciclo <= 12:
                raise HTTPException(422, "El ciclo debe estar entre 1 y 12.")

        if nombre_rol == "PROFESIONAL":
            for facultad_id in (datos.facultades or []):
                existe_facultad = conn.execute(
                    text("SELECT id FROM facultad WHERE id = :id"),
                    {"id": facultad_id}
                ).first()

                if not existe_facultad:
                    raise HTTPException(404, f"Facultad {facultad_id} no encontrada.")

        usuario_id = conn.execute(
            text("""
                INSERT INTO usuario (
                    rol_id, correo, contrasena_hash, nombres, apellidos, activo
                )
                VALUES (
                    :rol, :correo, :clave, :nombres, :apellidos, TRUE
                )
            """),
            {
                "rol": rol_id_db,
                "correo": correo,
                "clave": hash_clave(datos.contrasena),
                "nombres": nombres,
                "apellidos": apellidos
            }
        ).lastrowid

        if nombre_rol == "ESTUDIANTE":
            codigo = datos.codigo.strip() if datos.codigo else None

            if not codigo:
                numero = 1
                while conn.execute(
                    text("SELECT id FROM estudiante WHERE codigo = :codigo"),
                    {"codigo": f"EST-{numero:04d}"}
                ).first():
                    numero += 1
                codigo = f"EST-{numero:04d}"

            conn.execute(
                text("""
                    INSERT INTO estudiante (
                        usuario_id, facultad_id, codigo, ciclo
                    )
                    VALUES (:usuario, :facultad, :codigo, :ciclo)
                """),
                {
                    "usuario": usuario_id,
                    "facultad": datos.facultad_id,
                    "codigo": codigo,
                    "ciclo": datos.ciclo
                }
            )

        elif nombre_rol == "PROFESIONAL":
            profesional_id = conn.execute(
                text("""
                    INSERT INTO profesional (
                        usuario_id, numero_colegiatura, especialidad
                    )
                    VALUES (:usuario, :colegiatura, :especialidad)
                """),
                {
                    "usuario": usuario_id,
                    "colegiatura": datos.numero_colegiatura or None,
                    "especialidad": datos.especialidad or None
                }
            ).lastrowid

            for facultad_id in set(datos.facultades or []):
                conn.execute(
                    text("""
                        INSERT INTO profesional_facultad (
                            profesional_id, facultad_id
                        )
                        VALUES (:profesional, :facultad)
                    """),
                    {
                        "profesional": profesional_id,
                        "facultad": facultad_id
                    }
                )

        registrar(
            conn,
            int(token["sub"]),
            "USUARIO_CREADO",
            "usuario",
            usuario_id
        )

    return {
        "mensaje": "Usuario creado correctamente.",
        "id": usuario_id
    }

@router.patch("/usuarios/{usuario_id}")
def editar_usuario(
    usuario_id: int,
    datos: UsuarioPatchIn,
    token: dict = Depends(solo_admin)
):
    valores = datos.model_dump(exclude_unset=True)

    with engine.begin() as conn:
        usuario = conn.execute(
            text("""
                SELECT u.id, r.nombre AS rol
                FROM usuario u
                JOIN rol r ON r.id = u.rol_id
                WHERE u.id = :id
            """),
            {"id": usuario_id}
        ).mappings().first()

        if not usuario:
            raise HTTPException(404, "Usuario no encontrado.")

        nombre_rol = usuario["rol"]
        campos = {}

        for campo in ("nombres", "apellidos"):
            if campo in valores:
                valor = valores[campo].strip()
                if not valor:
                    raise HTTPException(422, f"{campo} es obligatorio.")
                campos[campo] = valor

        if "contrasena" in valores and valores["contrasena"]:
            if len(valores["contrasena"]) < 8:
                raise HTTPException(422, "La contraseña debe tener al menos 8 caracteres.")
            campos["contrasena_hash"] = hash_clave(valores["contrasena"])

        if "activo" in valores:
            campos["activo"] = valores["activo"]

        if valores.get("desbloquear"):
            campos["intentos_fallidos"] = 0
            campos["bloqueado_hasta"] = None

        if campos:
            sets = ", ".join(f"{campo} = :{campo}" for campo in campos)
            conn.execute(
                text(f"UPDATE usuario SET {sets} WHERE id = :id"),
                {**campos, "id": usuario_id}
            )

        if nombre_rol == "ESTUDIANTE":
            perfil = conn.execute(
                text("SELECT id FROM estudiante WHERE usuario_id = :id"),
                {"id": usuario_id}
            ).mappings().first()

            if perfil:
                cambios = {}

                if "facultad_id" in valores:
                    facultad = conn.execute(
                        text("SELECT id FROM facultad WHERE id = :id"),
                        {"id": valores["facultad_id"]}
                    ).first()
                    if not facultad:
                        raise HTTPException(404, "Facultad no encontrada.")
                    cambios["facultad_id"] = valores["facultad_id"]

                if "ciclo" in valores:
                    ciclo = valores["ciclo"]
                    if ciclo is not None and not 1 <= ciclo <= 12:
                        raise HTTPException(422, "El ciclo debe estar entre 1 y 12.")
                    cambios["ciclo"] = ciclo

                if cambios:
                    sets = ", ".join(f"{campo} = :{campo}" for campo in cambios)
                    conn.execute(
                        text(f"UPDATE estudiante SET {sets} WHERE usuario_id = :id"),
                        {**cambios, "id": usuario_id}
                    )

        elif nombre_rol == "PROFESIONAL":
            profesional = conn.execute(
                text("SELECT id FROM profesional WHERE usuario_id = :id"),
                {"id": usuario_id}
            ).mappings().first()

            if profesional:
                profesional_id = profesional["id"]
                cambios = {}

                if "especialidad" in valores:
                    cambios["especialidad"] = valores["especialidad"] or None

                if "numero_colegiatura" in valores:
                    cambios["numero_colegiatura"] = valores["numero_colegiatura"] or None

                if cambios:
                    sets = ", ".join(f"{campo} = :{campo}" for campo in cambios)
                    conn.execute(
                        text(f"UPDATE profesional SET {sets} WHERE id = :id"),
                        {**cambios, "id": profesional_id}
                    )

                if "facultades" in valores:
                    nuevas = set(valores["facultades"] or [])

                    for facultad_id in nuevas:
                        existe = conn.execute(
                            text("SELECT id FROM facultad WHERE id = :id"),
                            {"id": facultad_id}
                        ).first()
                        if not existe:
                            raise HTTPException(404, f"Facultad {facultad_id} no encontrada.")

                    conn.execute(
                        text("DELETE FROM profesional_facultad WHERE profesional_id = :id"),
                        {"id": profesional_id}
                    )

                    for facultad_id in nuevas:
                        conn.execute(
                            text("""
                                INSERT INTO profesional_facultad (profesional_id, facultad_id)
                                VALUES (:profesional, :facultad)
                            """),
                            {"profesional": profesional_id, "facultad": facultad_id}
                        )

        registrar(
            conn,
            int(token["sub"]),
            "USUARIO_EDITADO",
            "usuario",
            usuario_id
        )

    return {"mensaje": "Usuario actualizado correctamente."}


# ============================================================
# FACULTADES
# ============================================================

@router.get("/facultades")
def listar_facultades(token: dict = Depends(solo_admin)):
    with engine.connect() as conn:
        filas = conn.execute(
            text("""
                SELECT
                    f.id,
                    f.nombre,
                    COUNT(DISTINCT s.id) AS estudiantes,
                    COUNT(DISTINCT a.id) AS alertas
                FROM facultad f
                LEFT JOIN estudiante s
                    ON s.facultad_id = f.id
                LEFT JOIN evaluacion e
                    ON e.estudiante_id = s.id
                LEFT JOIN alerta a
                    ON a.evaluacion_id = e.id
                GROUP BY f.id, f.nombre
                ORDER BY f.nombre
            """)
        ).mappings().all()

    return [dict(f) for f in filas]

@router.post("/facultades")
def crear_facultad(datos: dict, token: dict = Depends(solo_admin)):
    nombre = str(datos.get("nombre", "")).strip()

    if not nombre:
        raise HTTPException(
            status_code=400,
            detail="El nombre de la facultad es obligatorio."
        )

    with engine.begin() as conn:
        # La instalacion inicial crea una universidad con AUTO_INCREMENT.
        # No puede suponerse que su identificador sera siempre 1.
        universidad_id = conn.execute(
            text("SELECT id FROM universidad ORDER BY id LIMIT 1")
        ).scalar()
        if universidad_id is None:
            raise HTTPException(
                status_code=409,
                detail="No existe ninguna universidad registrada. Inicializa los datos base antes de crear facultades."
            )

        existente = conn.execute(
            text("""
                SELECT id
                FROM facultad
                WHERE LOWER(nombre) = LOWER(:nombre)
                  AND universidad_id = :universidad_id
            """),
            {"nombre": nombre, "universidad_id": universidad_id}
        ).first()

        if existente:
            raise HTTPException(
                status_code=409,
                detail="Esta facultad ya existe."
            )

        resultado = conn.execute(
            text("""
                INSERT INTO facultad (universidad_id, nombre)
                VALUES (:universidad_id, :nombre)
            """),
            {"nombre": nombre, "universidad_id": universidad_id}
        )

        facultad_id = resultado.lastrowid

        registrar(
            conn,
            int(token["sub"]),
            "CREAR",
            "facultad",
            facultad_id
        )

    return {
        "mensaje": "Facultad creada correctamente.",
        "id": facultad_id,
        "nombre": nombre
    }


# ============================================================
# REPORTE PROFESIONAL PDF
# ============================================================

@router.get("/reportes/profesionales/pdf")
def generar_pdf_profesional(
    token: dict = Depends(solo_admin)
):
    with engine.connect() as conn:

        # Estadísticas generales
        estadisticas = conn.execute(
            text("""
                SELECT
                    (
                        SELECT COUNT(*)
                        FROM usuario
                        WHERE rol_id = (
                            SELECT id
                            FROM rol
                            WHERE nombre = 'ESTUDIANTE'
                        )
                    ) AS estudiantes,

                    (
                        SELECT COUNT(*)
                        FROM usuario
                        WHERE rol_id = (
                            SELECT id
                            FROM rol
                            WHERE nombre = 'PROFESIONAL'
                        )
                    ) AS profesionales,

                    (
                        SELECT COUNT(*)
                        FROM evaluacion
                    ) AS evaluaciones_totales,

                    (
                        SELECT COUNT(*)
                        FROM evaluacion
                        WHERE nivel_riesgo = 'ALTO'
                    ) AS evaluaciones_alto,

                    (
                        SELECT COUNT(*)
                        FROM evaluacion
                        WHERE nivel_riesgo = 'MEDIO'
                    ) AS evaluaciones_medio,

                    (
                        SELECT COUNT(*)
                        FROM evaluacion
                        WHERE nivel_riesgo = 'BAJO'
                    ) AS evaluaciones_bajo,

                    (
                        SELECT COUNT(*)
                        FROM alerta
                        WHERE estado = 'NUEVA'
                    ) AS casos_nuevos,

                    (
                        SELECT COUNT(*)
                        FROM alerta
                        WHERE estado = 'EN_REVISION'
                    ) AS en_revision,

                    (
                        SELECT COUNT(*)
                        FROM alerta
                        WHERE estado IN ('ATENDIDA', 'DESCARTADA')
                    ) AS cerrados
            """)
        ).mappings().first()

        # Estadísticas por facultad
        por_facultad = conn.execute(
            text("""
                SELECT
                    f.nombre AS facultad,
                    COUNT(DISTINCT e.id) AS evaluaciones,
                    COUNT(DISTINCT CASE
                        WHEN a.estado IN ('ATENDIDA', 'DESCARTADA')
                        THEN a.id
                    END) AS evaluaciones_cerradas
                FROM facultad f
                LEFT JOIN estudiante s
                    ON s.facultad_id = f.id
                LEFT JOIN evaluacion e
                    ON e.estudiante_id = s.id
                LEFT JOIN alerta a
                    ON a.evaluacion_id = e.id
                GROUP BY f.id, f.nombre
                ORDER BY f.nombre
            """)
        ).mappings().all()

        # Estadísticas por profesional
        por_profesional = conn.execute(
            text("""
                SELECT
                    up.nombres,
                    up.apellidos,
                    COUNT(DISTINCT a.id) AS casos_asignados,
                    COUNT(DISTINCT CASE
                        WHEN a.estado = 'ATENDIDA'
                        THEN a.id
                    END) AS casos_atendidos,
                    COUNT(DISTINCT CASE
                        WHEN a.estado = 'DESCARTADA'
                        THEN a.id
                    END) AS casos_descartados
                FROM usuario up
                JOIN profesional p
                    ON p.usuario_id = up.id
                LEFT JOIN alerta a
                    ON a.profesional_id = p.id
                WHERE up.activo = TRUE
                GROUP BY up.id, up.nombres, up.apellidos
                ORDER BY casos_asignados DESC
                LIMIT 10
            """)
        ).mappings().all()

    # PDF real: el endpoint antes devolvia JSON pese a terminar en /pdf.
    salida = BytesIO()
    pdf = canvas.Canvas(salida, pagesize=A4)
    ancho, alto = A4
    y = alto - 55
    pdf.setTitle("Mente Sana AQP - Reporte administrativo")
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(45, y, "Mente Sana AQP - Reporte administrativo")
    y -= 23
    pdf.setFont("Helvetica", 9)
    pdf.drawString(45, y, "Generado: " + datetime.now().strftime("%d/%m/%Y %H:%M"))
    y -= 33

    def linea(texto, encabezado=False):
        nonlocal y
        if y < 55:
            pdf.showPage()
            y = alto - 55
        pdf.setFont("Helvetica-Bold" if encabezado else "Helvetica", 10)
        pdf.drawString(45, y, str(texto)[:100])
        y -= 19

    linea("Indicadores generales", True)
    for clave, valor in dict(estadisticas).items():
        linea(f"{clave.replace('_', ' ').capitalize()}: {valor}")
    y -= 9
    linea("Por facultad", True)
    for f in por_facultad:
        linea(f"{f['facultad']}: {f['evaluaciones']} evaluaciones, {f['evaluaciones_cerradas']} cerradas")
    y -= 9
    linea("Por profesional", True)
    for p in por_profesional:
        linea(f"{p['nombres']} {p['apellidos']}: {p['casos_asignados']} asignados, {p['casos_atendidos']} atendidos")
    pdf.save()
    salida.seek(0)
    return StreamingResponse(
        salida,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="reporte_administrativo.pdf"'},
    )
