import { useCallback, useEffect, useState } from "react";
import { api, mensajeError } from "../../api";

export default function Reportes() {
  const [datos, setDatos] = useState(null);
  const [error, setError] = useState("");
  const [descargando, setDescargando] = useState(false);

  const cargar = useCallback(async () => {
    try {
      const r = await api.get("/reportes/facultad");
      setDatos(r.data);
    } catch (err) {
      setError(mensajeError(err, "No se pudieron cargar los reportes."));
    }
  }, []);

  useEffect(() => { cargar(); }, [cargar]);

async function descargarPdf() {
  setDescargando(true);
  setError("");

  try {
    const res = await api.get("/reportes/facultad/pdf", {
      responseType: "blob"
    });

    const blob = new Blob([res.data], {
      type: "application/pdf"
    });

    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");

    a.href = url;
    a.download = `reporte_profesional_${new Date().toISOString().slice(0, 10)}.pdf`;

    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);

    URL.revokeObjectURL(url);

  } catch (err) {
    setError(mensajeError(err, "No se pudo generar el PDF."));
  } finally {
    setDescargando(false);
  }
}

  if (!datos) {
    return <>{error ? <div className="mensaje error" role="alert">{error}</div> : <p className="suave">Cargando reportes...</p>}</>;
  }

  return (
    <>
      <div className="cabecera">
        <div><h1>Reportes de mi facultad</h1><p className="suave">Resumen de atención psicológica - {datos.facultad}</p></div>
        <button className="btn" onClick={descargarPdf} disabled={descargando}>
          {descargando ? "Generando PDF..." : "Exportar reporte (JasperReports)"}
        </button>
      </div>

      {error && <div className="mensaje error" role="alert">{error}</div>}

      <div className="kpis" style={{ marginBottom: 18 }}>
        <div className="kpi"><div className="valor">{datos.total_evaluaciones}</div><div className="etiqueta">Evaluaciones registradas</div></div>
        <div className="kpi petroleo"><div className="valor">{datos.estudiantes_activos}</div><div className="etiqueta">Estudiantes activos</div></div>
        <div className="kpi"><div className="valor">{datos.casos_nuevos}</div><div className="etiqueta">Casos nuevos</div></div>
        <div className="kpi terracota"><div className="valor">{datos.porcentaje_casos_resueltos}%</div><div className="etiqueta">Tasa resolución</div></div>
      </div>

      <div className="tarjeta">
        <h3>Resumen</h3>
        <div className="grid2" style={{ marginBottom: 12 }}>
          <div className="campo"><label>Evaluaciones cerradas</label><input type="text" value={datos.evaluaciones_cerradas} readOnly /></div>
          <div className="campo"><label>En revisión</label><input type="text" value={datos.en_revision} readOnly /></div>
          <div className="campo"><label>Casos resueltos</label><input type="text" value={datos.casos_resueltos} readOnly /></div>
          <div className="campo"><label>Puntaje promedio</label><input type="text" value={datos.puntaje_promedio.toFixed(2)} readOnly /></div>
        </div>
      </div>

      <div className="tarjeta">
        <h3>Por profesional</h3>
        {datos.por_profesional.length === 0 && <p className="vacio">No hay datos por profesional.</p>}
        {datos.por_profesional.length > 0 && (
          <div className="tabla-contenedor">
            <table>
              <thead>
                <tr>
                  <th>Profesional</th>
                  <th>Casos asignados</th>
                  <th>Casos atendidos</th>
                  <th>Casos descartados</th>
                </tr>
              </thead>
              <tbody>
                {datos.por_profesional.map((p, i) => (
                  <tr key={i}>
                    <td><strong>{p.nombres} {p.apellidos}</strong></td>
                    <td>{p.casos_asignados}</td>
                    <td><span className="chip ok">{p.casos_atendidos}</span></td>
                    <td><span className="chip petroleo">{p.casos_descartados}</span></td>
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