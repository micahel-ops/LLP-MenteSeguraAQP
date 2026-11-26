"""Mente Sana AQP - API (FastAPI).  Ejecutar:  python -m uvicorn main:app --reload"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from db import engine  # noqa: F401  (crear_usuarios.py y cargar_cuestionarios.py lo importan desde aquí)
import rutas_admin
import rutas_auth
import rutas_estudiante
import rutas_profesional

app = FastAPI(title="Mente Sana AQP - API")

app.add_middleware(
      CORSMiddleware,
      allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
      allow_credentials=True,   # <-- agregar esto
      allow_methods=["*"],
      allow_headers=["*"],
)

for modulo in (rutas_auth, rutas_estudiante, rutas_profesional, rutas_admin):
    app.include_router(modulo.router)
