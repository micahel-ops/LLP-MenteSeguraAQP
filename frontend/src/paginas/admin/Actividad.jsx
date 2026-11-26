import { useEffect, useState } from "react";
import { api, fecha, mensajeError } from "../../api";

const NOMBRES = {
  LOGIN: "Inicio de sesión", LOGIN_FALLIDO: "Intento de ingreso fallido", EVALUACION_ENVIADA: "Evaluación enviada",
  CONSENTIMIENTO_ACEPTADO: "Consentimiento aceptado", CASO_TOMADO: "Caso tomado", REVISION_INICIADA: "Revisión iniciada",
  SEGUIMIENTO_REGISTRADO: "Seguimiento registrado", ALERTA_VALIDADA: "Alerta validada", USUARIO_CREADO: "Usuario creado",
  USUARIO_EDITADO: "Usuario editado", CASO_ASIGNADO: "Caso asignado", FACULTAD_CREADA: "Facultad creada",
};

export default function Actividad() {
  const [filas, setFilas] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api.get("/admin/actividad", { params: { limite: 100 } })
      .then((r) => setFilas(r.data))
      .catch((err) => setError(mensajeError(err, "No se pudo cargar la actividad.")));
  }, []);

  return (
    <>
      <div className="cabecera"><div><h1>Registro de actividad</h1><p className="suave">Las últimas 100 acciones registradas en la plataforma.</p></div></div>
      {error && <div className="mensaje error" role="alert">{error}</div>}
      <div className="tarjeta">
        {filas && filas.length === 0 && <p className="vacio">Todavía no hay actividad registrada.</p>}
        {filas && filas.length > 0 && (
          <div className="tabla-contenedor">
            <table>
              <thead><tr><th>Fecha</th><th>Usuario</th><th>Acción</th><th>Elemento</th></tr></thead>
              <tbody>
                {filas.map((f) => (
                  <tr key={f.id}>
                    <td>{fecha(f.fecha, true)}</td>
                    <td>{f.correo || "—"}</td>
                    <td>{NOMBRES[f.accion] || f.accion}</td>
                    <td>{f.entidad ? `${f.entidad} #${f.entidad_id ?? ""}` : "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </>
  );
}
