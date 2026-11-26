"""Contraseñas (bcrypt), tokens (JWT) y control de acceso por rol."""
import os
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from dotenv import load_dotenv
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

load_dotenv()
SECRET = os.getenv("JWT_SECRET", "cambia-esta-clave")
HORAS_SESION = 8
esquema = HTTPBearer(auto_error=False)


def hash_clave(clave: str) -> str:
    return bcrypt.hashpw(clave.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def clave_correcta(clave: str, hash_guardado: str) -> bool:
    try:
        return bcrypt.checkpw(clave.encode("utf-8"), hash_guardado.encode("utf-8"))
    except ValueError:
        return False


def crear_token(usuario_id: int, rol: str) -> str:
    vence = datetime.now(timezone.utc) + timedelta(hours=HORAS_SESION)
    return jwt.encode({"sub": str(usuario_id), "rol": rol, "exp": vence}, SECRET, algorithm="HS256")


def usuario_actual(cred: HTTPAuthorizationCredentials = Depends(esquema)):
    if cred is None:
        raise HTTPException(401, "Falta el token")
    try:
        return jwt.decode(cred.credentials, SECRET, algorithms=["HS256"])
    except jwt.PyJWTError:
        raise HTTPException(401, "Token inválido o vencido")


def requiere(*roles):
    """Dependencia: solo deja pasar a los roles indicados."""
    def comprobar(token: dict = Depends(usuario_actual)):
        if token["rol"] not in roles:
            raise HTTPException(403, "No tienes permiso para esta acción")
        return token
    return comprobar
