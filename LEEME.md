# Mente Sana AQP — proyecto completo (backend + frontend)

> **Guía actualizada:** consultar primero [INICIAR_AQUI.md](INICIAR_AQUI.md).
> Las instrucciones siguientes pertenecen a la estructura original y pueden estar desactualizadas.

Usa tu MISMA base de datos MySQL `sdtr` (27 tablas) y tu MISMA estructura de carpetas
(`sdtr/backend` y `sdtr/frontend`). No cambia ninguna tabla ni instala librerías nuevas.

## 1. Qué archivos copiar

### Backend  (carpeta `sdtr/backend`)
| Archivo | Acción |
|---|---|
| `main.py` | REEMPLAZAR (ahora solo arma la API) |
| `db.py` | NUEVO (conexión a MySQL y registro de actividad) |
| `seguridad.py` | NUEVO (contraseñas, tokens y roles) |
| `nlp.py` | NUEVO (motor de análisis de texto en español) |
| `reglas.py` | NUEVO (categorías, niveles, etapas del flujo y mensajes) |
| `casos.py` | NUEVO (consulta común de casos) |
| `rutas_auth.py`, `rutas_estudiante.py`, `rutas_profesional.py`, `rutas_admin.py` | NUEVOS |
| `nlp_prueba.py` | NUEVO (prueba del motor de texto desde la terminal) |
| `crear_usuarios.py`, `cargar_cuestionarios.py`, `.env`, `requirements.txt` | los que ya tienes; no hace falta tocarlos |

### Frontend  (carpeta `sdtr/frontend`)
| Archivo | Acción |
|---|---|
| `index.html` | REEMPLAZAR |
| `src/index.css` | REEMPLAZAR |
| `src/App.jsx` | REEMPLAZAR |
| `src/api.js` | REEMPLAZAR |
| `src/main.jsx` | igual que el tuyo (puedes dejarlo) |
| `src/componentes/` (`Logo`, `Layout`, `Etapas`, `Graficos`) | CARPETA NUEVA |
| `src/paginas/Login.jsx` | NUEVO |
| `src/paginas/estudiante/` (`Inicio`, `Evaluacion`) | CARPETA NUEVA |
| `src/paginas/profesional/` (`Bandeja`, `Caso`) | CARPETA NUEVA |
| `src/paginas/admin/` (`Panel`, `Usuarios`, `Casos`, `Actividad`) | CARPETA NUEVA |

BORRAR de `frontend/src` (ya no se usan): `Login.jsx`, `Layout.jsx`, `EstudianteInicio.jsx`, `Evaluacion.jsx`,
`ProfesionalAlertas.jsx`, `ProfesionalAlertaDetalle.jsx`, `App.css`.

## 2. Cómo ejecutarlo
Terminal 1 (backend):
    cd sdtr\backend
    .\venv\Scripts\python.exe -m uvicorn main:app --reload
Terminal 2 (frontend):
    cd sdtr\frontend
    npm run dev
Luego abre http://localhost:5173

Cuentas de prueba (clave `Demo2026!`): estudiante@demo.pe, profesional@demo.pe, admin@demo.pe.
Si todavía no existen, ejecuta una vez `.\venv\Scripts\python.exe crear_usuarios.py`.

## 3. Qué revisar primero
1. http://127.0.0.1:8000/api/salud responde con los 3 roles.
2. En la pantalla de login aparecen botones de "Cuentas de demostración" (solo en desarrollo).
3. Entra como administrador y mira el panel general.
4. Prueba el motor de texto:  .\venv\Scripts\python.exe nlp_prueba.py
