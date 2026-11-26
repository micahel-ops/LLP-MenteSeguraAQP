import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, CLASE_NIVEL, fecha, mensajeError, NIVEL_ESTUDIANTE, SEGUIMIENTO_ESTUDIANTE } from "../../api";

export default function Inicio() {
  const [resumen, setResumen] = useState(null);
  const [lista, setLista] = useState(null);
  const [error, setError] = useState("");
  const [acepto, setAcepto] = useState(false);
  const [guardando, setGuardando] = useState(false);

  const cargar = useCallback(async () => {
    try {
      const [a, b] = await Promise.all([api.get("/estudiante/resumen"), api.get("/mis-evaluaciones")]);
      setResumen(a.data);
      setLista(b.data);
    } catch (err) {
      setError(mensajeError(err, "No se pudo cargar tu información."));
    }
  }, []);
  useEffect(() => { cargar(); }, [cargar]);

  async function aceptar() {
    setGuardando(true);
    try {
      await api.post("/estudiante/consentimiento");
      await cargar();
    } catch (err) {
      setError(mensajeError(err));
    } finally {
      setGuardando(false);
    }
  }

  if (!resumen) return <>{error ? <div className="mensaje error" role="alert">{error}</div> : <p className="suave">Cargando...</p>}</>;
  const { perfil, ultima } = resumen;

  return (
    <>
      <div className="cabecera">
        <div>
          <h1>Hola, {perfil.nombres}</h1>
          <p className="suave">{perfil.facultad} · ciclo {perfil.ciclo ?? "—"} · código {perfil.codigo}</p>
        </div>
        {perfil.consentimiento_aceptado && <Link className="btn" to="/estudiante/evaluar">Nueva evaluación</Link>}
      </div>
      {error && <div className="mensaje error" role="alert">{error}</div>}

      {!perfil.consentimiento_aceptado && (
        <div className="tarjeta calida" style={{ marginBottom: 20 }}>
          <h3>Antes de comenzar: consentimiento informado</h3>
          <p>
            Mente Sana AQP usa tus respuestas para identificar a tiempo señales de malestar y coordinar apoyo con
            profesionales de salud mental de tu universidad. Tus datos se tratan de forma confidencial según la Ley N.º 29733
            de Protección de Datos Personales. Esta herramienta no emite diagnósticos ni reemplaza la atención profesional.
          </p>
          <label style={{ display: "flex", gap: 8, alignItems: "center", margin: "10px 0 14px", fontWeight: 700 }}>
            <input type="checkbox" checked={acepto} onChange={(e) => setAcepto(e.target.checked)} />
            He leído y acepto el consentimiento informado
          </label>
          <button className="btn petroleo" disabled={!acepto || guardando} onClick={aceptar}>Aceptar y continuar</button>
        </div>
      )}

      <div className="kpis">
        <div className="kpi"><div className="valor">{ultima ? fecha(ultima.fecha) : "—"}</div><div className="etiqueta">Última evaluación</div></div>
        <div className="kpi terracota"><div className="valor">{ultima ? NIVEL_ESTUDIANTE[ultima.nivel] : "—"}</div><div className="etiqueta">Estado según tu última evaluación</div></div>
        <div className="kpi petroleo"><div className="valor">{resumen.total}</div><div className="etiqueta">Evaluaciones realizadas</div></div>
        <div className="kpi"><div className="valor">{resumen.proxima_reevaluacion ? fecha(resumen.proxima_reevaluacion) : "—"}</div><div className="etiqueta">Próxima reevaluación sugerida</div></div>
      </div>

      <div className="cols">
        <div className="tarjeta">
          <h3>Tu historial</h3>
          {lista && lista.length === 0 && <p className="vacio">Aún no has hecho ninguna evaluación.</p>}
          {lista && lista.length > 0 && (
            <div className="tabla-contenedor">
              <table>
                <thead><tr><th>Fecha</th><th>Cuestionario</th><th>Resultado</th><th>Estado</th><th>Seguimiento</th></tr></thead>
                <tbody>
                  {lista.map((e) => (
                    <tr key={e.id}>
                      <td>{fecha(e.fecha)}</td>
                      <td>{e.instrumento}</td>
                      <td>{e.categoria} ({e.puntaje} pts)</td>
                      <td><span className={`chip ${CLASE_NIVEL[e.nivel]}`}>{NIVEL_ESTUDIANTE[e.nivel]}</span></td>
                      <td>{SEGUIMIENTO_ESTUDIANTE[e.seguimiento]}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
        <div className="col">
          <div className="tarjeta">
            <h3>Para cuidarte cada día</h3>
            <ul className="lista-suave">
              <li>Mantén una rutina de sueño regular.</li>
              <li>Practica 10 minutos de respiración guiada.</li>
              <li>Conversa con alguien de confianza.</li>
              <li>Conoce los servicios de bienestar de tu universidad.</li>
            </ul>
          </div>
          <div className="tarjeta oscura">
            <h3>¿Necesitas ayuda ahora?</h3>
            <p>Llama a la Línea 113 (Minsa). Los resultados de esta herramienta son un apoyo, no un diagnóstico.</p>
          </div>
        </div>
      </div>
    </>
  );
}
