import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, ESTADO_ALERTA, fecha, mensajeError } from "../../api";

export default function Seguimientos() {
  const [alertas, setAlertas] = useState(null);
  const [error, setError] = useState("");
  const [filtroEstado, setFiltroEstado] = useState("todos");

  const cargar = useCallback(async () => {
    try {
      const r = await api.get("/alertas", { params: { filtro: "mios" } });
      setAlertas(r.data.alertas);
    } catch (err) {
      setError(mensajeError(err, "No se pudieron cargar los seguimientos."));
    }
  }, []);

  useEffect(() => { cargar(); }, [cargar]);

  if (!alertas) {
    return <>{error ? <div className="mensaje error" role="alert">{error}</div> : <p className="suave">Cargando seguimientos...</p>}</>;
  }

  const filtrados = alertas.filter((a) => {
    if (filtroEstado === "activos") return a.estado === "EN_REVISION" || a.estado === "NUEVA";
    if (filtroEstado === "cerrados") return a.estado === "ATENDIDA" || a.estado === "DESCARTADA";
    return true;
  });

  return (
    <>
      <div className="cabecera">
        <div><h1>Mis seguimientos</h1><p className="suave">Consolidado de casos en atención y controles de seguimiento.</p></div>
      </div>

      {error && <div className="mensaje error" role="alert">{error}</div>}

      <div className="tarjeta" style={{ marginBottom: 18 }}>
        <h3>Filtrar casos</h3>
        <div className="pestanas" role="tablist" style={{ marginTop: 8 }}>
          <button className={`pestana ${filtroEstado === "todos" ? "activa" : ""}`} onClick={() => setFiltroEstado("todos")}>Todos ({alertas.length})</button>
          <button className={`pestana ${filtroEstado === "activos" ? "activa" : ""}`} onClick={() => setFiltroEstado("activos")}>En proceso ({alertas.filter(a => a.estado === "EN_REVISION" || a.estado === "NUEVA").length})</button>
          <button className={`pestana ${filtroEstado === "cerrados" ? "activa" : ""}`} onClick={() => setFiltroEstado("cerrados")}>Concluidos ({alertas.filter(a => a.estado === "ATENDIDA" || a.estado === "DESCARTADA").length})</button>
        </div>
      </div>

      <div className="tarjeta">
        {filtrados.length === 0 && <p className="vacio">No hay casos en este estado.</p>}
        {filtrados.length > 0 && (
          <div className="tabla-contenedor">
            <table>
              <thead>
                <tr>
                  <th>Prioridad</th>
                  <th>Estudiante</th>
                  <th>Facultad</th>
                  <th>Motivo</th>
                  <th>Etapa actual</th>
                  <th>Estado</th>
                  <th>Acción</th>
                </tr>
              </thead>
              <tbody>
                {filtrados.map((a) => (
                  <tr key={a.id} className={a.estado === "ATENDIDA" || a.estado === "DESCARTADA" ? "fila-cerrada" : ""}>
                    <td><span className="chip terracota">{a.prioridad}</span></td>
                    <td><strong>{a.estudiante}</strong></td>
                    <td>{a.facultad}</td>
                    <td>{a.motivo}</td>
                    <td>{a.etapa_nombre}</td>
                    <td><span className={`chip ${a.estado === "ATENDIDA" ? "petroleo" : a.estado === "DESCARTADA" ? "suave" : "aviso"}`}>{ESTADO_ALERTA[a.estado]}</span></td>
                    <td><Link className="enlace" to={`/profesional/casos/${a.id}`}>Ver detalle</Link></td>
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