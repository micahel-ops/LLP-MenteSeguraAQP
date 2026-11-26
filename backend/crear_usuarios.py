from datetime import datetime

import bcrypt
from sqlalchemy import text

from main import engine

CLAVE = "Demo2026!"


def obtener_o_crear(conn, select_sql, params, insert_sql, insert_params):
    fila = conn.execute(text(select_sql), params).first()
    if fila:
        return fila[0]
    return conn.execute(text(insert_sql), insert_params).lastrowid


hash_clave = bcrypt.hashpw(CLAVE.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

with engine.begin() as conn:
    uni = obtener_o_crear(
        conn, "SELECT id FROM universidad WHERE nombre = :n", {"n": "Universidad Demo"},
        "INSERT INTO universidad (nombre) VALUES (:n)", {"n": "Universidad Demo"},
    )
    fac = obtener_o_crear(
        conn, "SELECT id FROM facultad WHERE universidad_id = :u AND nombre = :n",
        {"u": uni, "n": "Ingeniería"},
        "INSERT INTO facultad (universidad_id, nombre) VALUES (:u, :n)",
        {"u": uni, "n": "Ingeniería"},
    )
    demo = [
        ("ESTUDIANTE", "estudiante@demo.pe", "Camila", "Quispe"),
        ("PROFESIONAL", "profesional@demo.pe", "Lucía", "Paredes"),
        ("ADMINISTRADOR", "admin@demo.pe", "Mario", "Condori"),
    ]
    for rol, correo, nombres, apellidos in demo:
        rol_id = conn.execute(text("SELECT id FROM rol WHERE nombre = :n"), {"n": rol}).scalar()
        uid = obtener_o_crear(
            conn, "SELECT id FROM usuario WHERE correo = :c", {"c": correo},
            """INSERT INTO usuario (rol_id, correo, contrasena_hash, nombres, apellidos)
               VALUES (:r, :c, :h, :n, :a)""",
            {"r": rol_id, "c": correo, "h": hash_clave, "n": nombres, "a": apellidos},
        )
        if rol == "ESTUDIANTE":
            obtener_o_crear(
                conn, "SELECT id FROM estudiante WHERE usuario_id = :u", {"u": uid},
                """INSERT INTO estudiante (usuario_id, facultad_id, codigo, ciclo,
                       consentimiento_aceptado, fecha_consentimiento)
                   VALUES (:u, :f, 'EST-0001', 6, TRUE, :d)""",
                {"u": uid, "f": fac, "d": datetime.now()},
            )
        elif rol == "PROFESIONAL":
            obtener_o_crear(
                conn, "SELECT id FROM profesional WHERE usuario_id = :u", {"u": uid},
                "INSERT INTO profesional (usuario_id, especialidad) VALUES (:u, 'Psicología clínica')",
                {"u": uid},
            )

print("Listo. Usuarios de prueba (clave de todos:", CLAVE + "):")
for _, correo, _, _ in demo:
    print(" -", correo)
