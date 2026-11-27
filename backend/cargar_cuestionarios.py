from sqlalchemy import text

from main import engine

STEM = "Durante las últimas 2 semanas, ¿con qué frecuencia le han molestado los siguientes problemas?"
OPCIONES = [("Nunca", 0), ("Varios días", 1), ("Más de la mitad de los días", 2), ("Casi todos los días", 3)]
ABIERTA = "Cuéntanos con tus propias palabras cómo te has sentido en las últimas dos semanas."

PHQ9 = [
    "Poco interés o placer en hacer las cosas",
    "Se ha sentido decaído(a), deprimido(a) o sin esperanzas",
    "Dificultad para dormir o para seguir durmiendo, o ha dormido demasiado",
    "Se ha sentido cansado(a) o con poca energía",
    "Poco apetito o ha comido en exceso",
    "Se ha sentido mal consigo mismo(a), o que es un fracaso, o que ha quedado mal con usted mismo(a) o con su familia",
    "Dificultad para concentrarse en cosas como leer o ver televisión",
    "Se ha movido o hablado tan lento que otras personas lo han notado, o lo contrario: ha estado muy inquieto(a) o agitado(a)",
    "Pensamientos de que estaría mejor muerto(a) o de lastimarse de alguna manera",
]
GAD7 = [
    "Se ha sentido nervioso(a), ansioso(a) o muy alterado(a)",
    "No ha podido dejar de preocuparse o controlar la preocupación",
    "Se ha preocupado demasiado por diferentes cosas",
    "Ha tenido dificultad para relajarse",
    "Ha estado tan inquieto(a) que le es difícil quedarse quieto(a)",
    "Se ha molestado o irritado fácilmente",
    "Ha sentido miedo, como si algo terrible fuera a pasar",
]

with engine.begin() as conn:
    for codigo, items, nombre, tipo, maximo in (
        ("PHQ9", PHQ9, "Cuestionario de salud del paciente (PHQ-9)", "DEPRESION", 27),
        ("GAD7", GAD7, "Escala de ansiedad generalizada (GAD-7)", "ANSIEDAD", 21),
    ):
        ins = conn.execute(text("SELECT id FROM instrumento WHERE codigo = :c"), {"c": codigo}).scalar()
        if ins is None:
            ins = conn.execute(
                text("""INSERT INTO instrumento (codigo, nombre, tipo, puntaje_maximo)
                        VALUES (:c, :n, :t, :m)"""),
                {"c": codigo, "n": nombre, "t": tipo, "m": maximo},
            ).lastrowid
        if conn.execute(text("SELECT COUNT(*) FROM pregunta WHERE instrumento_id = :i"), {"i": ins}).scalar():
            print(codigo, "ya tenía preguntas, no se tocó")
            continue
        for n, enunciado in enumerate(items, start=1):
            pid = conn.execute(
                text("""INSERT INTO pregunta (instrumento_id, numero, enunciado, tipo, obligatoria)
                        VALUES (:i, :n, :e, 'CERRADA', TRUE)"""),
                {"i": ins, "n": n, "e": enunciado},
            ).lastrowid
            for orden, (texto, puntaje) in enumerate(OPCIONES, start=1):
                conn.execute(
                    text("INSERT INTO opcion_respuesta (pregunta_id, texto, puntaje, orden) VALUES (:p, :t, :s, :o)"),
                    {"p": pid, "t": texto, "s": puntaje, "o": orden},
                )
        conn.execute(
            text("""INSERT INTO pregunta (instrumento_id, numero, enunciado, tipo, obligatoria)
                    VALUES (:i, :n, :e, 'ABIERTA', TRUE)"""),
            {"i": ins, "n": len(items) + 1, "e": ABIERTA},
        )
        print(codigo, "cargado:", len(items), "preguntas cerradas y 1 abierta")
