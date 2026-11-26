from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text

from db import engine, registrar
from seguridad import clave_correcta, crear_token, usuario_actual

router = APIRouter(prefix="/api")
MAX_INTENTOS = 5
BLOQUEO_MIN = 15


@router.get("/salud")
def salud():
    with engine.connect() as conn:
        roles = conn.execute(text("SELECT nombre FROM rol")).scalars().all()
    return {"estado": "ok", "roles": roles}


class LoginIn(BaseModel):
    correo: str
    contrasena: str


@router.post("/login")
def login(datos: LoginIn):
    ahora = datetime.now()
    fallo = False
    with engine.begin() as conn:
        u = conn.execute(
            text("""SELECT u.id, u.correo, u.nombres, u.apellidos, u.contrasena_hash, u.activo,
                           u.intentos_fallidos, u.bloqueado_hasta, r.nombre AS rol
                    FROM usuario u JOIN rol r ON r.id = u.rol_id WHERE u.correo = :c"""),
            {"c": datos.correo.strip().lower()},
        ).mappings().first()
        if u is None or not u["activo"]:
            raise HTTPException(401, "Correo o contraseña incorrectos")
        if u["bloqueado_hasta"] and u["bloqueado_hasta"] > ahora:
            raise HTTPException(423, "Cuenta bloqueada temporalmente. Intenta más tarde")

        if clave_correcta(datos.contrasena, u["contrasena_hash"]):
            conn.execute(
                text("""UPDATE usuario SET intentos_fallidos = 0, bloqueado_hasta = NULL, ultimo_acceso = :a
                        WHERE id = :id"""), {"a": ahora, "id": u["id"]})
            registrar(conn, u["id"], "LOGIN", "usuario", u["id"])
        else:
            intentos = u["intentos_fallidos"] + 1
            bloqueo = ahora + timedelta(minutes=BLOQUEO_MIN) if intentos >= MAX_INTENTOS else None
            conn.execute(
                text("UPDATE usuario SET intentos_fallidos = :i, bloqueado_hasta = :b WHERE id = :id"),
                {"i": intentos, "b": bloqueo, "id": u["id"]})
            registrar(conn, u["id"], "LOGIN_FALLIDO", "usuario", u["id"])
            fallo = True
    if fallo:  # se lanza fuera del bloque para que el intento fallido quede guardado
        raise HTTPException(401, "Correo o contraseña incorrectos")
    return {
        "token": crear_token(u["id"], u["rol"]),
        "usuario": {"id": u["id"], "nombres": u["nombres"], "apellidos": u["apellidos"],
                    "correo": u["correo"], "rol": u["rol"]},
    }


@router.get("/yo")
def yo(token: dict = Depends(usuario_actual)):
    return {"id": int(token["sub"]), "rol": token["rol"]}
