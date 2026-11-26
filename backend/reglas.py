"""Reglas del negocio: categorías, niveles de riesgo, etapas del flujo y mensajes."""
import re

CATEGORIAS = {
    "PHQ9": [(4, "Mínima"), (9, "Leve"), (14, "Moderada"), (19, "Moderadamente severa"), (27, "Severa")],
    "GAD7": [(4, "Mínima"), (9, "Leve"), (14, "Moderada"), (21, "Severa")],
}
NIVELES = {"BAJO": 0, "MEDIO": 1, "ALTO": 2}


def categoria(codigo, puntaje):
    for tope, nombre in CATEGORIAS[codigo]:
        if puntaje <= tope:
            return nombre
    return CATEGORIAS[codigo][-1][1]


def nivel_instrumento(puntaje, critica):
    """Nivel por puntaje (provisional: se confirma con los profesionales)."""
    if critica or puntaje >= 15:
        return "ALTO"
    if puntaje >= 10:
        return "MEDIO"
    return "BAJO"


def mayor(a, b):
    return a if NIVELES[a] >= NIVELES[b] else b


# --- Flujo del caso (inspirado en BPMN) -------------------------------------
ETAPAS = {1: "Evaluación registrada", 2: "Análisis y revisión", 3: "Seguimiento y derivación", 4: "Cerrado y control"}
TIPOS_SEGUIMIENTO = ("CONTACTO", "DERIVACION", "CONTROL")


def etapa_caso(estado, n_seguimientos):
    if estado in ("ATENDIDA", "DESCARTADA"):
        return 4
    if n_seguimientos > 0:
        return 3
    if estado == "EN_REVISION":
        return 2
    return 1


def empaquetar_seguimiento(tipo, texto):
    return f"[{tipo}] {texto.strip()}"


def desempaquetar_seguimiento(descripcion):
    m = re.match(r"^\[(CONTACTO|DERIVACION|CONTROL)\]\s*(.*)$", descripcion or "", re.S)
    return (m.group(1), m.group(2)) if m else ("CONTACTO", descripcion or "")


def estado_para_estudiante(estado_alerta):
    if estado_alerta is None:
        return "NINGUNO"
    if estado_alerta == "NUEVA":
        return "PENDIENTE"
    if estado_alerta == "EN_REVISION":
        return "EN_SEGUIMIENTO"
    return "CERRADO"


# --- Mensajes para el estudiante ---------------------------------------------
MENSAJES = {
    "BAJO": {"titulo": "Vas por buen camino",
             "texto": "Tus respuestas muestran pocas señales de malestar en este momento. Seguir cuidando tu rutina te ayuda a mantenerte bien."},
    "MEDIO": {"titulo": "Conviene prestar atención",
              "texto": "Notamos algunas señales de malestar. Te sugerimos conversar con alguien de confianza y cuidar tu descanso. Te propondremos una nueva evaluación en unas semanas."},
    "ALTO": {"titulo": "Gracias por contarlo",
             "texto": "Tus respuestas indican que sería muy útil hablar pronto con un profesional. Tu resultado quedó disponible para revisión de un profesional de salud mental. Si necesitas ayuda ahora, llama a la Línea 113 (Minsa)."},
}
RECOMENDACIONES = {
    "BAJO": ["Mantén una rutina de sueño regular.", "Reserva tiempo para actividades que disfrutes.",
             "Sigue en contacto con tus amistades y tu familia."],
    "MEDIO": ["Conversa con alguien de confianza sobre cómo te sientes.", "Practica 10 minutos de respiración guiada al día.",
              "Organiza tus tareas en bloques pequeños para bajar la presión.", "Conoce los servicios de bienestar de tu universidad."],
    "ALTO": ["Habla pronto con un profesional de salud mental o con alguien de confianza.",
             "Llama a la Línea 113 (Minsa) si necesitas apoyo ahora.", "No te quedes solo(a) con lo que sientes: pide compañía.",
             "Acércate al servicio de bienestar o psicología de tu universidad."],
}
