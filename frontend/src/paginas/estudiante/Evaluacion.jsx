import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, fecha, mensajeError } from "../../api";

const INTRO = "Durante las últimas 2 semanas, ¿con qué frecuencia le han molestado los siguientes problemas?";

export default function Evaluacion() {
  const [instrumentos, setInstrumentos] = useState(null);
  const [cuestionario, setCuestionario] = useState(null);
  const [elegidas, setElegidas] = useState({});
  const [textos, setTextos] = useState({});
  const [resultado, setResultado] = useState(null);
  const [error, setError] = useState("");
  const [cargando, setCargando] = useState(false);

  useEffect(() => {
    api.get("/instrumentos")
      .then((r) => setInstrumentos(r.data))
      .catch((err) => setError(mensajeError(err, "No se pudieron cargar los cuestionarios.")));
  }, []);

  async function abrir(codigo) {
    setError("");
    setCargando(true);
    try {
      const { data } = await api.get(`/instrumentos/${codigo}`);
      setCuestionario(data);
      setElegidas({});
      setTextos({});
    } catch (err) {
      setError(mensajeError(err, "No se pudo cargar el cuestionario."));
    } finally {
      setCargando(false);
    }
  }

  const preguntas = cuestionario ? cuestionario.preguntas : [];
  const respondidas = preguntas.filter((p) => (p.tipo === "CERRADA" ? elegidas[p.id] : (textos[p.id] || "").trim())).length;
  const completo = preguntas.length > 0 && respondidas === preguntas.length;

  async function enviar() {
    setError("");
    setCargando(true);
    try {
      const respuestas = preguntas.map((p) =>
        p.tipo === "CERRADA"
          ? { pregunta_id: p.id, opcion_id: elegidas[p.id] }
          : { pregunta_id: p.id, texto_libre: textos[p.id].trim() }
      );
      const { data } = await api.post("/evaluaciones", { instrumento: cuestionario.instrumento.codigo, respuestas });
      setResultado(data);
    } catch (err) {
      setError(mensajeError(err, "No se pudo enviar la evaluación. Revisa tus respuestas."));
    } finally {
      setCargando(false);
    }
  }

  // 3. Resultado
  if (resultado) {
    return (
      <>
        <div className="cabecera"><div><h1>Gracias por responder</h1><p className="suave">Resultado preliminar: {resultado.categoria} ({resultado.puntaje} puntos)</p></div></div>
        <div className="tarjeta" style={{ marginBottom: 16 }}>
          <h3>{resultado.mensaje.titulo}</h3>
          <p>{resultado.mensaje.texto}</p>
          {resultado.reevaluacion && <p className="nota">Te sugerimos una nueva evaluación hacia el {fecha(resultado.reevaluacion)}.</p>}
          <p className="nota">Es un apoyo para ti, no un diagnóstico. Solo un profesional de salud mental puede valorar tu situación.</p>
        </div>
        {resultado.mostrar_ayuda && (
          <div className="tarjeta oscura" role="alert" style={{ marginBottom: 16 }}>
            <h3>No estás solo(a)</h3>
            <p>Si necesitas ayuda ahora, llama a la Línea 113 (Minsa) o acércate a alguien de confianza.</p>
          </div>
        )}
        <div className="tarjeta" style={{ marginBottom: 16 }}>
          <h3>Recomendaciones para ti</h3>
          <ul className="lista-suave">{resultado.recomendaciones.map((r) => <li key={r}>{r}</li>)}</ul>
        </div>
        <Link className="btn" to="/estudiante">Volver al inicio</Link>
      </>
    );
  }

  // 1. Elegir cuestionario
  if (!cuestionario) {
    return (
      <>
        <div className="cabecera"><div><h1>Nueva evaluación</h1><p className="suave">Elige el cuestionario que quieres responder. Toma pocos minutos.</p></div></div>
        {error && <div className="mensaje error" role="alert">{error}</div>}
        {error.includes("consentimiento") && <p><Link className="enlace" to="/estudiante">Ir a aceptar el consentimiento</Link></p>}
        {instrumentos && instrumentos.length === 0 && <p className="vacio">No hay cuestionarios disponibles.</p>}
        <div className="kpis">
          {(instrumentos || []).map((i) => (
            <button key={i.codigo} className="eleccion" disabled={cargando} onClick={() => abrir(i.codigo)}>
              <span className="valor">{i.codigo === "PHQ9" ? "PHQ-9" : i.codigo === "GAD7" ? "GAD-7" : i.codigo}</span>
              <span>{i.tipo === "DEPRESION" ? "Estado de ánimo" : "Ansiedad"}</span>
              <span className="nota" style={{ display: "block" }}>{i.preguntas} preguntas</span>
            </button>
          ))}
        </div>
      </>
    );
  }

  // 2. Responder
  return (
    <>
      <div className="cabecera"><div><h1>{cuestionario.instrumento.nombre}</h1><p className="suave">{INTRO}</p></div></div>
      <div className="progreso" role="progressbar" aria-valuemin={0} aria-valuemax={preguntas.length} aria-valuenow={respondidas}
           aria-label="Preguntas respondidas"><span style={{ width: `${(respondidas / preguntas.length) * 100}%` }} /></div>
      {preguntas.map((p) => (
        <fieldset key={p.id} className="pregunta">
          <legend>{p.numero}. {p.enunciado}</legend>
          {p.tipo === "CERRADA" ? (
            <div className="opciones">
              {p.opciones.map((o) => (
                <label key={o.id} className={elegidas[p.id] === o.id ? "opcion sel" : "opcion"}>
                  <input type="radio" name={`p${p.id}`} checked={elegidas[p.id] === o.id}
                         onChange={() => setElegidas({ ...elegidas, [p.id]: o.id })} />
                  {o.texto}
                </label>
              ))}
            </div>
          ) : (
            <>
              <textarea rows={5} value={textos[p.id] || ""} aria-label={p.enunciado}
                        placeholder="Escribe aquí con tus propias palabras..."
                        onChange={(e) => setTextos({ ...textos, [p.id]: e.target.value })} />
              <p className="nota">Tu texto es analizado de forma automática para detectar señales de bienestar o malestar. No se usa para juzgarte.</p>
            </>
          )}
        </fieldset>
      ))}
      {error && <div className="mensaje error" role="alert">{error}</div>}
      <div className="fila-acciones">
        <button className="btn" disabled={!completo || cargando} onClick={enviar}>{cargando ? "Enviando..." : "Enviar evaluación"}</button>
        <button className="btn secundario" disabled={cargando} onClick={() => setCuestionario(null)}>Cambiar de cuestionario</button>
      </div>
    </>
  );
}
