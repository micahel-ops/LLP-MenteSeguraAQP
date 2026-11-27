# Mente Sana AQP — instalación para demostración

Esta es una aplicación web local para fines académicos. **Usar datos ficticios.**

## Opción A: todo con Docker Desktop (recomendada)

1. Instala e inicia Docker Desktop en Windows (si lo solicita, habilita WSL 2).
2. Descomprime el ZIP y abre PowerShell en la carpeta `LLP-MenteSeguraAQP` (donde está `compose.yaml`).
3. Ejecuta `docker compose up --build -d`. La primera instalación descargará imágenes y puede tardar.
4. Verifica el estado con `docker compose ps`. Deben figurar `db`, `backend` y `frontend` como funcionando.
5. Abre <http://localhost:5173>.

No necesitas instalar Python, Node ni MySQL en tu Windows para esta opción. La base se crea y los scripts de carga se ejecutan automáticamente **solo durante el primer inicio del volumen de MySQL**; los scripts Python también pueden ejecutarse otra vez sin duplicar sus registros iniciales.

Tres cuentas ficticias, todas con contraseña `Demo2026!`:

- `estudiante@demo.pe`
- `profesional@demo.pe`
- `admin@demo.pe`

API: <http://localhost:8000/docs>. Comprobación: <http://localhost:8000/api/salud>.

Pruebas unitarias de lógica (dentro del contenedor): `docker compose exec backend python -m unittest test_logica.py`.

Si el primer inicio demora, revisa `docker compose logs --tail=100 backend` y `docker compose logs --tail=100 db`.

Para detener: `docker compose down`. Los datos permanecen en el volumen.

**ATENCIÓN:** `docker compose down -v` elimina el volumen y todos los datos de la base de esta aplicación. No utilizarlo si deseas conservar datos.

MySQL se comunica con el backend por la red interna de Docker usando `db:3306`. No se publica el puerto de la base de datos en Windows, para evitar conflictos con puertos reservados y mantener el entorno de demostración local más aislado.

## Opción B: instalación manual con MySQL y Python/Node

Esta opción sirve si ya tienes MySQL en Windows. Nunca importes `schema.sql` sobre una base con datos que quieras conservar: contiene sentencias `DROP TABLE` y está destinado a una **base vacía**.

1. Crea una base nueva `sdtr` o asegúrate de que no contenga tablas que desees conservar.
2. En MySQL Workbench importa `database/schema.sql`, después `database/seed.sql`, en ese orden, utilizando la conexión MySQL correspondiente.
3. En `backend`, copia `.env.ejemplo` a `.env` y configura `DB_HOST`, `DB_PORT` (normalmente 3306), `DB_USER`, `DB_PASSWORD`, `DB_NAME=sdtr` y una clave `JWT_SECRET` propia. No compartas `.env`.
4. En PowerShell dentro de `backend`:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   .\.venv\Scripts\python.exe crear_usuarios.py
   .\.venv\Scripts\python.exe cargar_cuestionarios.py
   .\.venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000
   ```

5. En **otra** terminal, desde `frontend`:

   ```powershell
   npm ci
   npm run dev
   ```

6. Abre <http://localhost:5173>.

### Error `Unknown database 'sdtr'`

El servidor MySQL responde pero la base `sdtr` no existe todavía en esa conexión. Primero crea/importa el esquema. No ejecutes los scripts Python antes de crear las tablas y cargar los roles.

### Importante para el informe

El analizador de texto se basa en reglas heurísticas Python; **no es un modelo entrenado ni un diagnóstico clínico**. No se implementó recuperación automática de datos externos ni reentrenamiento. El manual solo describe funciones que existen en el código.
