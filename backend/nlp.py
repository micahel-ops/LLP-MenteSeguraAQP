"""Motor heurístico de análisis de texto en español (PLN local, sin internet).

Pasos: normaliza el texto (minúsculas, sin tildes), lo separa en palabras, busca
frases de un léxico por categorías, ajusta por negaciones ("no me siento triste"),
intensificadores ("muy cansado") y factores protectores, y devuelve un nivel de
señal (BAJO, MEDIO o ALTO) con las palabras que más influyeron.

Es un apoyo para el profesional: NO diagnostica.
"""
import re
import unicodedata

# categoría: (peso, frases)
LEXICO = {
    "CRISIS": (6.0, [
        "quiero morir", "quiero morirme", "quisiera morir", "quisiera morirme", "quitarme la vida",
        "acabar con mi vida", "acabar con todo", "terminar con mi vida", "suicidio", "suicidarme",
        "hacerme daño", "lastimarme", "cortarme", "no quiero vivir", "no quiero seguir viviendo",
        "mejor muerto", "mejor muerta", "quiero desaparecer", "ya no quiero estar aquí", "no quiero despertar",
    ]),
    "DESESPERANZA": (1.8, [
        "sin esperanza", "desesperanza", "desesperado", "desesperada", "no tiene sentido", "sin sentido",
        "no vale la pena", "inútil", "soy un fracaso", "soy una carga", "no sirvo", "no valgo",
        "no veo salida", "sin salida", "no puedo más", "no aguanto más", "estoy harto", "estoy harta",
        "vacío", "vacía",
    ]),
    "ANIMO_BAJO": (1.2, [
        "triste", "tristeza", "deprimido", "deprimida", "depresión", "llorar", "lloro", "llorando",
        "desanimado", "desanimada", "sin ganas", "sin ánimo", "sin motivación", "desmotivado", "desmotivada",
        "no tengo ganas", "apatía", "nada me gusta", "nada me emociona", "sin interés", "melancolía",
    ]),
    "ANSIEDAD": (1.2, [
        "ansioso", "ansiosa", "ansiedad", "nervioso", "nerviosa", "nervios", "ataque de pánico", "pánico",
        "angustia", "angustiado", "angustiada", "preocupado", "preocupada", "preocupación",
        "no puedo dejar de pensar", "me falta el aire", "taquicardia", "opresión en el pecho", "miedo",
        "temor", "inquieto", "inquieta", "tensión", "tenso", "tensa", "estrés", "estresado", "estresada",
        "agobiado", "agobiada", "agobio", "abrumado", "abrumada",
    ]),
    "SUENO": (0.8, [
        "insomnio", "no puedo dormir", "no duermo", "duermo mal", "duermo poco", "duermo demasiado",
        "pesadillas", "desvelado", "desvelada",
    ]),
    "FATIGA": (0.8, [
        "cansado", "cansada", "cansancio", "agotado", "agotada", "agotamiento", "sin energía", "fatiga",
        "sin fuerzas",
    ]),
    "APETITO": (0.6, ["no tengo hambre", "sin apetito", "no como", "como demasiado", "como mucho"]),
    "AISLAMIENTO": (1.2, [
        "me siento solo", "me siento sola", "estoy solo", "estoy sola", "muy solo", "muy sola", "soledad",
        "aislado", "aislada", "me aíslo", "no quiero ver a nadie", "no quiero salir", "nadie me entiende",
        "nadie me quiere", "abandonado", "abandonada",
    ]),
    "CONCENTRACION": (0.8, [
        "no puedo concentrarme", "no me concentro", "dificultad para concentrarme", "distraído", "distraída",
    ]),
    "ACADEMICO": (0.7, [
        "no rindo", "voy a desaprobar", "desaprobar", "bajo rendimiento", "carga académica",
        "presión de los exámenes", "voy a reprobar", "dejar la universidad", "abandonar los estudios",
    ]),
    "IRRITABILIDAD": (0.7, ["irritable", "me enojo fácil", "rabia", "estallo"]),
}
PROTECTORES = (1.0, [
    "me siento bien", "estoy bien", "muy bien", "tranquilo", "tranquila", "feliz", "contento", "contenta",
    "animado", "animada", "motivado", "motivada", "disfruto", "disfrutando", "apoyo de mi familia",
    "apoyo de mis amigos", "mis amigos", "con ganas", "duermo bien", "descanso bien", "relajado", "relajada",
    "optimista", "estoy mejor", "me siento mejor", "orgulloso", "orgullosa", "esperanza",
])

NEGADORES = {"no", "nunca", "jamas", "ni", "tampoco"}
INTENSIFICADORES = {"muy", "demasiado", "demasiada", "mucho", "mucha", "bastante", "extremadamente",
                    "totalmente", "completamente", "siempre", "constantemente"}
ATENUADORES = {"poco", "algo", "ligeramente", "levemente"}
UMBRAL_MEDIO = 2.5
UMBRAL_ALTO = 6.0


def normalizar(texto: str) -> str:
    sin_tildes = "".join(c for c in unicodedata.normalize("NFD", texto.lower()) if unicodedata.category(c) != "Mn")
    return sin_tildes


def tokens(texto: str):
    return re.findall(r"[a-z0-9]+", normalizar(texto))


def _construir_indice():
    indice = {}
    def agregar(frase, categoria, peso, protector=False):
        t = tuple(tokens(frase))
        indice.setdefault(t[0], []).append((t, categoria, peso, frase, protector))
    for categoria, (peso, frases) in LEXICO.items():
        for f in frases:
            agregar(f, categoria, peso)
    for f in PROTECTORES[1]:
        agregar(f, "PROTECTOR", PROTECTORES[0], protector=True)
    for lista in indice.values():
        lista.sort(key=lambda x: -len(x[0]))  # frases largas primero
    return indice


INDICE = _construir_indice()


def analizar_texto(texto: str) -> dict:
    palabras = tokens(texto or "")
    if not palabras:
        return {"nivel": "BAJO", "probabilidad": 0.0, "neto": 0.0, "critica": False, "sin_texto": True,
                "terminos": [], "categorias": {}, "palabras": 0}

    encontrados = {}  # (frase, categoria) -> [peso total, repeticiones]
    critica = False
    i = 0
    while i < len(palabras):
        coincidencia = None
        for t, categoria, peso, frase, protector in INDICE.get(palabras[i], []):
            if tuple(palabras[i:i + len(t)]) == t:
                coincidencia = (t, categoria, peso, frase, protector)
                break
        if coincidencia is None:
            i += 1
            continue
        t, categoria, peso, frase, protector = coincidencia
        previas = palabras[max(0, i - 3):i]
        negada = any(p in NEGADORES for p in previas)
        factor = 1.0
        if categoria != "CRISIS" and i > 0:
            if palabras[i - 1] in INTENSIFICADORES:
                factor = 1.3
            elif palabras[i - 1] in ATENUADORES:
                factor = 0.6

        if categoria == "CRISIS":
            critica = True
            clave, valor = (frase, "CRISIS"), peso
        elif protector and negada:
            clave, valor = ("no " + frase, "ANIMO_BAJO"), 0.8 * factor
        elif protector:
            clave, valor = (frase, "PROTECTOR"), -peso
        elif negada:
            clave, valor = None, 0.0  # "no me siento triste": se cancela
        else:
            clave, valor = (frase, categoria), peso * factor

        if clave is not None:
            actual = encontrados.setdefault(clave, [0.0, 0])
            actual[1] += 1
            decaimiento = {1: 1.0, 2: 0.5, 3: 0.25}.get(actual[1], 0.0)
            actual[0] += valor * decaimiento
        i += len(t)

    riesgo = sum(v for (_, c), (v, _) in encontrados.items() if c != "PROTECTOR")
    protector = -sum(v for (_, c), (v, _) in encontrados.items() if c == "PROTECTOR")
    neto = max(0.0, riesgo - 0.6 * protector)
    if critica or neto >= UMBRAL_ALTO:
        nivel = "ALTO"
    elif neto >= UMBRAL_MEDIO:
        nivel = "MEDIO"
    else:
        nivel = "BAJO"

    terminos = sorted(
        ({"termino": f, "categoria": c, "peso": round(v, 2)} for (f, c), (v, _) in encontrados.items() if v != 0),
        key=lambda x: -abs(x["peso"]),
    )[:10]
    categorias = {}
    for (f, c), (v, _) in encontrados.items():
        categorias[c] = round(categorias.get(c, 0.0) + v, 2)
    return {
        "nivel": nivel,
        "probabilidad": round(neto / (neto + 4.0), 4),
        "neto": round(neto, 2),
        "critica": critica,
        "sin_texto": False,
        "terminos": terminos,
        "categorias": categorias,
        "palabras": len(palabras),
    }
