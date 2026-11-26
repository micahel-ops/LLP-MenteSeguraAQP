"""Consulta y formato comunes de los casos (alertas), usados por profesional y administrador."""
import reglas
from db import iso

BASE_ALERTAS = """SELECT a.id, a.prioridad, a.motivo, a.estado, a.creada_en, a.profesional_id,
       e.nivel_riesgo, e.puntaje_instrumento AS puntaje, i.codigo AS instrumento,
       s.codigo AS estudiante, f.nombre AS facultad,
       up.nombres AS prof_nombres, up.apellidos AS prof_apellidos,
       (SELECT COUNT(*) FROM seguimiento sg WHERE sg.alerta_id = a.id) AS n_seguimientos
FROM alerta a
JOIN evaluacion e ON e.id = a.evaluacion_id
JOIN instrumento i ON i.id = e.instrumento_id
JOIN estudiante s ON s.id = e.estudiante_id
JOIN facultad f ON f.id = s.facultad_id
LEFT JOIN profesional pr ON pr.id = a.profesional_id
LEFT JOIN usuario up ON up.id = pr.usuario_id"""

ORDEN = " ORDER BY (a.estado IN ('NUEVA', 'EN_REVISION')) DESC, a.prioridad DESC, a.creada_en DESC"


def formatear(f, mi_id=None):
    etapa = reglas.etapa_caso(f["estado"], int(f["n_seguimientos"] or 0))
    asignado = None if f["profesional_id"] is None else f"{f['prof_nombres']} {f['prof_apellidos']}"
    return {
        "id": f["id"], "prioridad": float(f["prioridad"]), "motivo": f["motivo"], "estado": f["estado"],
        "creada_en": iso(f["creada_en"]), "nivel": f["nivel_riesgo"], "puntaje": f["puntaje"],
        "instrumento": f["instrumento"], "estudiante": f["estudiante"], "facultad": f["facultad"],
        "etapa": etapa, "etapa_nombre": reglas.ETAPAS[etapa],
        "profesional_id": f["profesional_id"], "asignado_a": asignado,
        "es_mio": mi_id is not None and f["profesional_id"] == mi_id,
    }


def resumen_estados(casos):
    return {
        "nuevas": sum(c["estado"] == "NUEVA" for c in casos),
        "en_revision": sum(c["estado"] == "EN_REVISION" for c in casos),
        "atendidas": sum(c["estado"] == "ATENDIDA" for c in casos),
        "descartadas": sum(c["estado"] == "DESCARTADA" for c in casos),
    }
