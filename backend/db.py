"""Conexión a MySQL (lee los datos del archivo .env) y utilidades comunes."""
import os
from datetime import datetime

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

url = URL.create(
    "mysql+pymysql",
    username=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST", "localhost"),
    port=int(os.getenv("DB_PORT", "3306")),
    database=os.getenv("DB_NAME"),
    query={"charset": "utf8mb4"},
)
engine = create_engine(url, pool_pre_ping=True)


def registrar(conn, usuario_id, accion, entidad=None, entidad_id=None):
    """Guarda una fila en registro_actividad (RF020)."""
    conn.execute(
        text(
            """INSERT INTO registro_actividad (usuario_id, accion, entidad, entidad_id, fecha)
               VALUES (:u, :a, :e, :i, :f)"""
        ),
        {"u": usuario_id, "a": accion, "e": entidad, "i": entidad_id, "f": datetime.now()},
    )


def iso(valor):
    """Fecha/hora como texto 'AAAA-MM-DD HH:MM:SS' (o None)."""
    if valor is None:
        return None
    if isinstance(valor, datetime):
        return valor.strftime("%Y-%m-%d %H:%M:%S")
    return str(valor)
