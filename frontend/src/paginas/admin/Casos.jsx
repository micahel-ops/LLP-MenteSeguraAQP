import { useCallback, useEffect, useState } from "react";
import { api, ESTADO_ALERTA, fecha, mensajeError } from "../../api";

export default function Casos() {
  const [datos, setDatos] = useState(null);
  const [error, setError] = useState("");
  const [aviso, setAviso] = useState("");

  const cargar = useCallback(async () => {
    try {
      const r = await api.get("/admin/casos");
      setDatos(r.data);
    } catch (err) {
      setError(mensajeError(err, "No se pudieron cargar los casos."));
    }
  }, []);
  useEffect(() => { cargar(); }, [cargar]);

  async function asignar(id, valor) {
    setError(""); setAviso("");
    try {
      await api.post(`/admin/casos/${id}/asignar`, { profesional_id: valor ? Number(valor) : null });
      setAviso("Asignación actualizada.");
      await cargar();
    } catch (err) {
      setError(mensajeError(err));
    }
  }

  if (!datos) return <>{error ? <div className="mensaje error" role="alert">{error}</div> : <p className="suave">Cargando...</p>}</>;
  const r = datos.resumen;

  return (
    <>
      <div className="cabecera"><div><h1>Supervisión de casos</h1><p className="suave">Asigna casos a los profesionales y revisa en qué etapa del flujo está cada uno.</p></div></div>
      <div className="kpis">
        <div className="kpi terracota"><div className="valor">{r.nuevas}</div><div className="etiqueta">Nuevos</div></div>
        <div className="kpi"><div className="valor">{r.en_revision}</div><div className="etiqueta">En revisión o seguimiento</div></div>
        <div className="kpi petroleo"><div className="valor">{r.atendidas + r.descartadas}</div><div className="etiqueta">Cerrados</div></div>
      </div>
      {aviso && <div className="mensaje ok" role="status">{aviso}</div>}
      {error && <div className="mensaje error" role="alert">{error}</div>}
      <div className="tarjeta">
        {datos.casos.length === 0 && <p className="vacio">No hay casos registrados.</p>}
        {datos.casos.length > 0 && (
          <div className="tabla-contenedor">
            <table>
              <thead><tr><th>Estudiante</th><th>Facultad</th><th>Motivo</th><th>Etapa</th><th>Creado</th><th>Profesional asignado</th></tr></thead>
              <tbody>
                {datos.casos.map((c) => {
                  const cerrado = c.estado === "ATENDIDA" || c.estado === "DESCARTADA";
                  return (
                    <tr key={c.id} className={cerrado ? "fila-cerrada" : ""}>
                      <td><strong>{c.estudiante}</strong><div className="nota">Prioridad {c.prioridad}</div></td>
                      <td>{c.facultad}</td>
                      <td>{c.motivo}</td>
                      <td><span className={`chip ${c.etapa === 4 ? "petroleo" : "aviso"}`}>{c.etapa_nombre}</span><div className="nota">{ESTADO_ALERTA[c.estado]}</div></td>
                      <td>{fecha(c.creada_en)}</td>
                      <td>
                        {cerrado ? (
                          <span className="chip petroleo">
                            {c.asignado_a || "Sin asignar"}
                            </span>
                            ) : (
                            <select
                            aria-label={`Profesional del caso ${c.estudiante}`}
                            
                            value={c.profesional_id ?? ""}
                            onChange={(e) => asignar(c.id, e.target.value)}
                            >
                              <option value="">Sin asignar</option>
                              {datos.profesionales.map((p) => (
                                <option key={p.id} value={p.id}>
                                  {p.nombre}
                                  </option>
                                ))}
                                </select>
                              )}
                              </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </>
  );
}
