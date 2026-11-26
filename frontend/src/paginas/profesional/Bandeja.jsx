import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, ESTADO_ALERTA, mensajeError } from "../../api";

const PESTANAS = [["todos", "Todos"], ["mios", "Mis casos"], ["sin_asignar", "Sin asignar"]];

export default function Bandeja() {
  const [filtro, setFiltro] = useState("todos");
  const [datos, setDatos] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api.get("/alertas", { params: { filtro } })
      .then((r) => { setDatos(r.data); setError(""); })
      .catch((err) => setError(mensajeError(err, "No se pudieron cargar los casos.")));
  }, [filtro]);

  const r = datos ? datos.resumen : null;
  const c = datos ? datos.contadores : null;

  return (
    <>
      <div className="cabecera">
        <div><h1>Bandeja de casos</h1><p className="suave">Ordenados por prioridad. Los casos abiertos aparecen primero.</p></div>
      </div>

      <div className="kpis">
        <div className="kpi terracota"><div className="valor">{r ? r.nuevas : "—"}</div><div className="etiqueta">Casos nuevos</div></div>
        <div className="kpi"><div className="valor">{r ? r.en_revision : "—"}</div><div className="etiqueta">En revisión o seguimiento</div></div>
        <div className="kpi petroleo"><div className="valor">{r ? r.atendidas : "—"}</div><div className="etiqueta">Cerrados con riesgo confirmado</div></div>
        <div className="kpi"><div className="valor">{r ? r.descartadas : "—"}</div><div className="etiqueta">Descartados</div></div>
      </div>

      <div className="pestanas" role="tablist">
        {PESTANAS.map(([clave, texto]) => (
          <button key={clave} role="tab" aria-selected={filtro === clave} className={filtro === clave ? "pestana activa" : "pestana"}
                  onClick={() => setFiltro(clave)}>{texto}{c ? ` (${c[clave]})` : ""}</button>
        ))}
      </div>

      <div className="tarjeta">
        {error && <div className="mensaje error" role="alert">{error}</div>}
        {datos && datos.alertas.length === 0 && <p className="vacio">No hay casos en esta vista.</p>}
        {datos && datos.alertas.length > 0 && (
          <div className="tabla-contenedor">
            <table>
              <thead><tr><th>Prioridad</th><th>Estudiante</th><th>Facultad</th><th>Motivo</th><th>Etapa</th><th>Asignado a</th><th></th></tr></thead>
              <tbody>
                {datos.alertas.map((a) => (
                  <tr key={a.id} className={a.estado === "ATENDIDA" || a.estado === "DESCARTADA" ? "fila-cerrada" : ""}>
                    <td><span className="chip terracota">{a.prioridad}</span></td>
                    <td><strong>{a.estudiante}</strong></td>
                    <td>{a.facultad}</td>
                    <td>{a.motivo}</td>
                    <td><span className={`chip ${a.etapa === 4 ? "petroleo" : "aviso"}`}>{a.etapa_nombre}</span><div className="nota">{ESTADO_ALERTA[a.estado]}</div></td>
                    <td>{a.asignado_a ? (a.es_mio ? "Yo" : a.asignado_a) : <span className="suave">Sin asignar</span>}</td>
                    <td><Link className="enlace" to={`/profesional/casos/${a.id}`}>Abrir</Link></td>
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
