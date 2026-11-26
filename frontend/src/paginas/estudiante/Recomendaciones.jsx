import { useCallback, useEffect, useState } from "react";
import { api, CLASE_NIVEL, fecha, mensajeError, NIVEL_ESTUDIANTE, RECOMENDACIONES } from "../../api";

export default function Recomendaciones() {
  const [resumen, setResumen] = useState(null);
  const [evaluaciones, setEvaluaciones] = useState(null);
  const [error, setError] = useState("");

  const cargar = useCallback(async () => {
    try {
      const [r1, r2] = await Promise.all([
        api.get("/estudiante/resumen"),
        api.get("/mis-evaluaciones")
      ]);
      setResumen(r1.data);
      setEvaluaciones(r2.data);
    } catch (err) {
      setError(mensajeError(err, "No se pudo cargar la información."));
    }
  }, []);

  useEffect(() => { cargar(); }, [cargar]);

  if (!resumen) {
    return <>{error ? <div className="mensaje error" role="alert">{error}</div> : <p className="suave">Cargando...</p>}</>;
  }

  const { perfil, ultima } = resumen;
  const nivelActual = ultima?.nivel || "BAJO";
  const recomendaciones = RECOMENDACIONES[nivelActual];

  // Calcular tendencias
  const tendencia = evaluaciones && evaluaciones.length >= 2
    ? evaluaciones[0].puntaje - evaluaciones[evaluaciones.length - 1].puntaje
    : null;

  return (
    <>
      <div className="cabecera">
        <div><h1>Recomendaciones personalizadas</h1><p className="suave">Basadas en tu última evaluación y tu historial.</p></div>
      </div>

      {error && <div className="mensaje error" role="alert">{error}</div>}

      <div className="tarjeta" style={{ marginBottom: 18 }}>
        <h3>Tu estado actual</h3>
        <div style={{ display: "flex", gap: 16, alignItems: "center", flexWrap: "wrap" }}>
          <span className={`chip ${CLASE_NIVEL[nivelActual]}`} style={{ fontSize: "1rem" }}>
            {NIVEL_ESTUDIANTE[nivelActual]}
          </span>
          {ultima && <span className="nota">Última evaluación: {fecha(ultima.fecha)} · {ultima.instrumento}: {ultima.categoria} ({ultima.puntaje} pts)</span>}
          {tendencia !== null && (
            <span className={`nota ${tendencia > 0 ? "aviso" : tendencia < 0 ? "ok" : ""}`}>
              Cambio en el puntaje: {tendencia > 0 ? "+" : ""}{tendencia} pts
            </span>
          )}
        </div>
      </div>

      <div className="tarjeta" style={{ marginBottom: 18 }}>
        <h3>Recomendaciones para ti</h3>
        <p className="nota" style={{ marginBottom: 12 }}>
          Estas recomendaciones se adaptan automáticamente según tu nivel de riesgo actual.
        </p>
        <ul className="lista-suave">
          {recomendaciones.map((r, i) => (
            <li key={i} style={{ marginBottom: 8, lineHeight: 1.5 }}>{r}</li>
          ))}
        </ul>
      </div>

      <div className="tarjeta" style={{ marginBottom: 18 }}>
        <h3>Tu evolución reciente</h3>
        {evaluaciones && evaluaciones.length > 0 ? (
          <div className="tabla-contenedor">
            <table>
              <thead><tr><th>Fecha</th><th>Cuestionario</th><th>Puntaje</th><th>Categoría</th><th>Nivel</th></tr></thead>
              <tbody>
                {evaluaciones.slice(0, 10).map((e) => (
                  <tr key={e.id}>
                    <td>{fecha(e.fecha)}</td>
                    <td>{e.instrumento}</td>
                    <td>{e.puntaje}</td>
                    <td>{e.categoria}</td>
                    <td><span className={`chip ${CLASE_NIVEL[e.nivel]}`}>{NIVEL_ESTUDIANTE[e.nivel]}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="vacio">Aún no hay evaluaciones para mostrar evolución.</p>
        )}
      </div>

      <div className="tarjeta oscura">
        <h3>Recuerda</h3>
        <ul className="lista-suave">
          <li>Estas recomendaciones son una guía, no sustituyen la opinión de un profesional.</li>
          <li>Si sientes que tu situación empeora, busca ayuda cuanto antes.</li>
          <li>Línea 113 (Minsa): atención psicológica gratuita 24/7.</li>
          <li>Tu universidad cuenta con servicios de bienestar y psicología.</li>
        </ul>
      </div>
    </>
  );
}