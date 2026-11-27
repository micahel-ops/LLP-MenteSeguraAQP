# Estado de esta revisión académica

## Cambios aplicados

- `database/schema.sql`: se retiraron instrucciones GTID y de binlog propias de otro servidor; definiciones de trigger y vista sin el usuario fijo `root@localhost`. **Solo para importación inicial sobre base vacía**.
- `database/seed.sql`: inserción repetible de los tres roles.
- `backend/cargar_cuestionarios.py`: crea PHQ-9 y GAD-7 si aún no están registrados; carga preguntas y opciones sin duplicarlas.
- `backend/crear_usuarios.py`: vincula el profesional demo con la facultad para habilitar seguimiento y reportes.
- `backend/requirements.txt`: incluye ReportLab y Requests.
- `compose.yaml`, Dockerfiles y `.dockerignore`: estructura para levantar frontend, backend y MySQL de una vez. Base y datos iniciales automáticos en primera ejecución.
- `backend/rutas_admin.py`: devuelve un PDF verdadero en `/api/admin/reportes/profesionales/pdf`.
- `frontend/src/paginas/admin/ModeloNLP.jsx`: estado `RETIRADA` conforme a la base de datos.
- `frontend/src/paginas/profesional/Reportes.jsx`: etiqueta de PDF corregida; usa ReportLab, no JasperReports.
- `test_all.py`: puerto/prefijos API corregidos.
- `backend/test_logica.py`: cinco pruebas puras de Python sobre cálculo y análisis de texto.
- `INICIAR_AQUI.md` y `docs/Manual_Instalacion_Mente_Sana_AQP.pdf`: instrucciones para Windows.

## Evidencia verificada

- Los 14 archivos Python analizados son sintácticamente válidos.
- Las cinco pruebas unitarias de `backend/test_logica.py` pasan.
- `compose.yaml` se puede interpretar correctamente como YAML; define tres servicios.
- El manual PDF contiene dos páginas A4 renderizadas e inspeccionadas visualmente.
- El esquema conserva 27 `CREATE TABLE` y no contiene instrucciones `GTID_PURGED` ni `DEFINER=root@localhost`.

## Lo que TODAVÍA hay que comprobar en un Windows con Docker/MySQL

1. Ejecutar `docker compose up --build -d` y revisar que MySQL termine la importación del esquema.
2. Probar `http://localhost:8000/api/salud` y el login de los tres roles.
3. Completar una evaluación de prueba y comprobar alertas, seguimientos y ambos reportes PDF.
4. Validar frontend con compilación (`npm ci` y `npm run build`).
5. Comprobar conexión, CRUD, validaciones y permisos con pruebas de integración.

No se pudieron ejecutar esos pasos de integración en el entorno de revisión porque no tiene servidor MySQL ni Docker. **No se declara el producto como totalmente verificado.**

## Documentación final que resta alinear con el código

- Unificar el nombre Mente Sana AQP / MenteSegura AQP en informe y portada.
- RF020 y RNF002 tienen descripciones copiadas de otros requisitos.
- Describir el motor de NLP como heurístico: no se implementó reentrenamiento ni un modelo de ML validado.
- Eliminar o mover a trabajo futuro recuperación automática de fuentes, predicción de tendencias y exportaciones que no existan.
- Completar diagramas reales, mínimo cinco mockups, diccionario de las 27 tablas, matriz RF-pantalla-código-prueba, conclusiones y referencias APA.
- El historial Git de origen pertenece principalmente a una cuenta: conservarlo y hacer nuevos commits genuinos.
- Crear el informe final corregido en PDF y probar el manual en otra computadora.

Esta entrega contiene **código corregido y manual PDF**, no el informe académico final revisado.
