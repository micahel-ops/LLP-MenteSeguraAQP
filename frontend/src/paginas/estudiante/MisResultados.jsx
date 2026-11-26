import { useCallback, useEffect, useState } from "react";
import { api, CLASE_NIVEL, fecha, mensajeError, NIVEL_ESTUDIANTE } from "../../api";

export default function MisResultados() {
  const [evaluaciones, setEvaluaciones] = useState(null);
  const [error, setError] = useState("");

  const cargar = useCallback(async () => {
    try {
      const r = await api.get("/mis-evaluaciones");
      setEvaluaciones(r.data);
    } catch (err) {
      setError(mensajeError(err, "No se pudo cargar el historial de evaluaciones."));
    }
  }, []);

  useEffect(() => { cargar(); }, [cargar]);

  if (!evaluaciones) {
    return <>{error ? <div className="mensaje error" role="alert">{error}</div> : <p className="suave">Cargando resultados...</p>}</>;
  }

  return (
    <>
      <div className="cabecera">
        <div><h1>Mis resultados</h1><p className="suave">Historial completo de tus evaluaciones y su evolución.</p></div>
      </div>

      {error && <div className="mensaje error" role="alert">{error}</div>}

      <div className="tarjeta">
        {evaluaciones.length === 0 && <p className="vacio">Aún no has hecho ninguna evaluación.</p>}
        {evaluaciones.length > 0 && (
          <div className="tabla-contenedor">
            <table>
              <thead>
                <tr>
                  <th>Fecha</th>
                  <th>Cuestionario</th>
                  <th>Resultado</th>
                  <th>Nivel</th>
                  <th>Seguimiento</th>
                </tr>
              </thead>
              <tbody>
                {evaluaciones.map((e) => (
                  <tr key={e.id}>
                    <td>{fecha(e.fecha)}</td>
                    <td>{e.instrumento}</td>
                    <td>{e.categoria} ({e.puntaje} pts)</td>
                    <td><span className={`chip ${CLASE_NIVEL[e.nivel]}`}>{NIVEL_ESTUDIANTE[e.nivel]}</span></td>
                    <td>{e.seguimiento}</td>
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