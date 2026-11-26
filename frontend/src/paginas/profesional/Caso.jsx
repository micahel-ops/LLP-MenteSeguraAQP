import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api, CLASE_NIVEL, ESTADO_ALERTA, fecha, mensajeError, NIVEL_PROFESIONAL, TIPO_SEGUIMIENTO } from "../../api";
import Etapas from "../../componentes/Etapas";

export default function Caso() {
  const { id } = useParams();
  const [datos, setDatos] = useState(null);
  const [error, setError] = useState("");
  const [tipo, setTipo] = useState("CONTACTO");
  const [observacion, setObservacion] = useState("");
  const [justificacion, setJustificacion] = useState("");
  const [enviando, setEnviando] = useState(false);

  const cargar = useCallback(async () => {
    try {
      const r = await api.get(`/alertas/${id}`);
      setDatos(r.data);
    } catch (err) {
      setError(mensajeError(err, "No se pudo cargar el caso."));
    }
  }, [id]);
  useEffect(() => { cargar(); }, [cargar]);

  async function accion(peticion, limpiar) {
    setError("");
    setEnviando(true);
    try {
      await peticion();
      if (limpiar) limpiar();
      await cargar();
    } catch (err) {
      setError(mensajeError(err));
    } finally {
      setEnviando(false);
    }
  }

  if (!datos) {
    return <>{error ? <div className="mensaje error" role="alert">{error}</div> : <p className="suave">Cargando...</p>}<Link className="enlace" to="/profesional">Volver a la bandeja</Link></>;
  }

  const { alerta: a, respuestas, analisis, seguimientos, validacion, historial } = datos;
  const cerrado = a.estado === "ATENDIDA" || a.estado === "DESCARTADA";
  const cerradas = respuestas.filter((r) => r.tipo === "CERRADA");
  const abiertas = respuestas.filter((r) => r.tipo === "ABIERTA");

  return (
    <>
      <p><Link className="enlace" to="/profesional">← Volver a la bandeja</Link></p>
      <div className="cabecera">
        <div>
          <h1>Caso {a.estudiante}</h1>
          <p className="suave">{a.facultad} · ciclo {a.ciclo ?? "—"} · {a.instrumento_nombre} · prioridad {a.prioridad}</p>
        </div>
        <span className={`chip ${cerrado ? "petroleo" : "terracota"}`}>{ESTADO_ALERTA[a.estado]}</span>
      </div>

      <div className="tarjeta" style={{ marginBottom: 18 }}>
        <Etapas etapa={a.etapa} validacion={validacion} />
        <div className="fila-acciones" style={{ marginTop: 14 }}>
          {a.sin_asignar && <button className="btn petroleo" disabled={enviando} onClick={() => accion(() => api.post(`/alertas/${id}/tomar`))}>Tomar caso</button>}
          {a.estado === "NUEVA" && a.puede_actuar && <button className="btn" disabled={enviando} onClick={() => accion(() => api.post(`/alertas/${id}/revision`))}>Iniciar revisión</button>}
          {!a.puede_actuar && <span className="mensaje info" style={{ margin: 0 }}>Este caso está asignado a {a.asignado_a}.</span>}
          {a.asignado_a && a.puede_actuar && <span className="nota" style={{ alignSelf: "center" }}>Asignado a {a.es_mio ? "ti" : a.asignado_a}</span>}
        </div>
      </div>
      {error && <div className="mensaje error" role="alert">{error}</div>}

      <div className="cols">
        <div className="col">
          <div className="tarjeta">
            <h3>Resultado de la evaluación</h3>
            <p><strong>{a.categoria}</strong> · {a.puntaje} puntos · nivel <span className={`chip ${CLASE_NIVEL[a.nivel]}`}>{NIVEL_PROFESIONAL[a.nivel]}</span></p>
            <p className="suave">Motivo de la alerta: {a.motivo}</p>
            {a.variacion != null && <p className="nota">Cambio frente a la evaluación anterior: {a.variacion > 0 ? "+" : ""}{a.variacion} puntos.</p>}
            <div className="tabla-contenedor">
              <table>
                <thead><tr><th>N.º</th><th>Pregunta</th><th>Respuesta</th></tr></thead>
                <tbody>{cerradas.map((r) => <tr key={r.numero}><td>{r.numero}</td><td>{r.enunciado}</td><td>{r.opcion} ({r.puntaje})</td></tr>)}</tbody>
              </table>
            </div>
          </div>

          <div className="tarjeta">
            <h3>Análisis del texto libre (PLN)</h3>
            {abiertas.map((r) => <blockquote className="cita" key={r.numero}>{r.texto_libre}</blockquote>)}
            {analisis.map((an, i) => (
              <div key={i} style={{ marginTop: 14 }}>
                <p>Nivel de señales: <span className={`chip ${CLASE_NIVEL[an.nivel]}`}>{NIVEL_PROFESIONAL[an.nivel]}</span> · intensidad {Math.round(an.probabilidad * 100)} % <span className="nota">· modelo {an.modelo}</span></p>
                <div className="progreso" role="img" aria-label={`Intensidad ${Math.round(an.probabilidad * 100)} por ciento`}><span style={{ width: `${an.probabilidad * 100}%` }} /></div>
                <p className="nota">Palabras y frases que más influyeron:</p>
                <div>
                  {an.terminos.length === 0 && <span className="nota">No se encontraron señales en el texto.</span>}
                  {an.terminos.map((t) => (
                    <span key={t.termino} className={`chip ${t.peso < 0 ? "ok" : "alto"}`} style={{ marginRight: 6, marginBottom: 6 }}>
                      {t.termino} ({t.peso > 0 ? "+" : ""}{t.peso})
                    </span>
                  ))}
                </div>
              </div>
            ))}
            <p className="nota" style={{ marginTop: 12 }}>Apoyo a la decisión profesional, no un diagnóstico.</p>
          </div>

          <div className="tarjeta">
            <h3>Historial del estudiante</h3>
            <div className="tabla-contenedor">
              <table>
                <thead><tr><th>Fecha</th><th>Cuestionario</th><th>Resultado</th><th>Nivel</th></tr></thead>
                <tbody>{historial.map((h) => (
                  <tr key={h.id}><td>{fecha(h.fecha)}</td><td>{h.instrumento}</td><td>{h.categoria} ({h.puntaje})</td>
                    <td><span className={`chip ${CLASE_NIVEL[h.nivel]}`}>{NIVEL_PROFESIONAL[h.nivel]}</span></td></tr>
                ))}</tbody>
              </table>
            </div>
          </div>
        </div>

        <div className="col">
          <div className="tarjeta">
            <h3>Contacto</h3>
            <p><strong>{a.nombres} {a.apellidos}</strong></p>
            <p className="suave">{a.correo}</p>
          </div>

          <div className="tarjeta">
            <h3>Seguimiento</h3>
            {seguimientos.length === 0 && <p className="nota">Aún no hay observaciones registradas.</p>}
            {seguimientos.map((s, i) => (
              <div key={i} style={{ padding: "8px 0", borderBottom: "1px solid var(--linea)" }}>
                <span className="chip petroleo">{TIPO_SEGUIMIENTO[s.tipo]}</span> <span className="nota">{s.profesional} · {fecha(s.fecha, true)}</span>
                <p style={{ margin: "6px 0 0" }}>{s.descripcion}</p>
              </div>
            ))}
            {a.puede_actuar && (
              <div style={{ marginTop: 12 }}>
                <div className="campo">
                  <label htmlFor="tipo">Tipo de acción</label>
                  <select id="tipo" value={tipo} onChange={(e) => setTipo(e.target.value)}>
                    <option value="CONTACTO">Contacto con el estudiante</option>
                    <option value="DERIVACION">Derivación</option>
                    <option value="CONTROL">Control posterior</option>
                  </select>
                </div>
                <div className="campo">
                  <label htmlFor="obs">Observación</label>
                  <textarea id="obs" rows={3} value={observacion} placeholder="Describe lo realizado..." onChange={(e) => setObservacion(e.target.value)} />
                </div>
                <button className="btn" disabled={enviando || !observacion.trim() || (cerrado && tipo !== "CONTROL")}
                        onClick={() => accion(() => api.post(`/alertas/${id}/seguimiento`, { tipo, descripcion: observacion }), () => setObservacion(""))}>
                  Guardar observación
                </button>
                {cerrado && <p className="nota" style={{ marginTop: 6 }}>El caso está cerrado: solo se admiten controles.</p>}
              </div>
            )}
          </div>

          <div className="tarjeta">
            <h3>Cierre del caso</h3>
            {validacion ? (
              <>
                <p><span className={`chip ${validacion.confirma_riesgo ? "alto" : "ok"}`}>{validacion.confirma_riesgo ? "Riesgo confirmado" : "Alerta descartada"}</span></p>
                <p>{validacion.justificacion}</p>
                <p className="nota">{fecha(validacion.fecha, true)} · queda registrado para mejorar el modelo.</p>
              </>
            ) : a.puede_actuar ? (
              <>
                <div className="campo">
                  <label htmlFor="just">Justificación</label>
                  <textarea id="just" rows={3} value={justificacion} placeholder="Justifica tu decisión..." onChange={(e) => setJustificacion(e.target.value)} />
                </div>
                <div className="fila-acciones">
                  <button className="btn" disabled={enviando || !justificacion.trim()}
                          onClick={() => accion(() => api.post(`/alertas/${id}/validacion`, { confirma_riesgo: true, justificacion }), () => setJustificacion(""))}>Confirmar riesgo</button>
                  <button className="btn secundario" disabled={enviando || !justificacion.trim()}
                          onClick={() => accion(() => api.post(`/alertas/${id}/validacion`, { confirma_riesgo: false, justificacion }), () => setJustificacion(""))}>Descartar alerta</button>
                </div>
              </>
            ) : <p className="nota">Solo el profesional asignado puede cerrar este caso.</p>}
          </div>
        </div>
      </div>
    </>
  );
}
