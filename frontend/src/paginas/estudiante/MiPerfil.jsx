import { useCallback, useEffect, useState } from "react";
import { api, mensajeError, fecha } from "../../api";

export default function MiPerfil() {
  const [resumen, setResumen] = useState(null);
  const [error, setError] = useState("");
  const [aviso, setAviso] = useState("");
  const [editando, setEditando] = useState(false);
  const [guardando, setGuardando] = useState(false);

  const [nombres, setNombres] = useState("");
  const [apellidos, setApellidos] = useState("");
  const [correo, setCorreo] = useState("");
  const [contrasena, setContrasena] = useState("");
  const [confirmar, setConfirmar] = useState("");

  const cargar = useCallback(async () => {
    try {
      const r = await api.get("/estudiante/resumen");
      const p = r.data.perfil;
      setNombres(p.nombres);
      setApellidos(p.apellidos);
      setCorreo(p.correo || "");
      setResumen(r.data);
    } catch (err) {
      setError(mensajeError(err, "No se pudo cargar el perfil."));
    }
  }, []);

  useEffect(() => { cargar(); }, [cargar]);

  async function guardar() {
    setError(""); setAviso(""); setGuardando(true);
    try {
      const cuerpo = { nombres: nombres.trim(), apellidos: apellidos.trim() };
      if (contrasena) {
        if (contrasena.length < 8) throw new Error("La contraseña debe tener al menos 8 caracteres");
        if (contrasena !== confirmar) throw new Error("Las contraseñas no coinciden");
        cuerpo.contrasena = contrasena;
      }
      await api.patch("/estudiante/perfil", cuerpo);
      setAviso("Perfil actualizado correctamente.");
      setContrasena(""); setConfirmar("");
      setEditando(false);
      await cargar();
    } catch (err) {
      setError(mensajeError(err));
    } finally {
      setGuardando(false);
    }
  }

  if (!resumen) {
    return <>{error ? <div className="mensaje error" role="alert">{error}</div> : <p className="suave">Cargando perfil...</p>}</>;
  }

  const { perfil, total, ultima, proxima_reevaluacion } = resumen;

  return (
    <>
      <div className="cabecera">
        <div><h1>Mi perfil</h1><p className="suave">Gestiona tus datos personales y configuración.</p></div>
      </div>

      {aviso && <div className="mensaje ok" role="status">{aviso}</div>}
      {error && <div className="mensaje error" role="alert">{error}</div>}

      <div className="tarjeta" style={{ marginBottom: 18 }}>
        <h3>Información académica</h3>
        <div className="grid2">
          <div className="campo">
            <label>Código de estudiante</label>
            <input type="text" value={perfil.codigo || "—"} readOnly />
          </div>
          <div className="campo">
            <label>Facultad</label>
            <input type="text" value={perfil.facultad || "—"} readOnly />
          </div>
          <div className="campo">
            <label>Ciclo</label>
            <input type="text" value={perfil.ciclo ? String(perfil.ciclo) : "—"} readOnly />
          </div>
          <div className="campo">
            <label>Consentimiento informado</label>
            <input type="text" value={perfil.consentimiento_aceptado ? "Aceptado" : "Pendiente"} readOnly />
          </div>
        </div>
      </div>

      <div className="tarjeta" style={{ marginBottom: 18 }}>
        <h3>Datos personales</h3>
        {editando ? (
          <form onSubmit={(e) => { e.preventDefault(); guardar(); }}>
            <div className="grid2">
              <div className="campo">
                <label htmlFor="nombres">Nombres</label>
                <input id="nombres" type="text" required value={nombres} onChange={(e) => setNombres(e.target.value)} />
              </div>
              <div className="campo">
                <label htmlFor="apellidos">Apellidos</label>
                <input id="apellidos" type="text" required value={apellidos} onChange={(e) => setApellidos(e.target.value)} />
              </div>
              <div className="campo">
                <label htmlFor="correo">Correo</label>
                <input id="correo" type="email" value={correo} readOnly />
                <span className="nota">El correo no se puede cambiar desde aquí.</span>
              </div>
              <div className="campo">
                <label htmlFor="contrasena">Nueva contraseña (opcional, mínimo 8 caracteres)</label>
                <input id="contrasena" type="password" value={contrasena} onChange={(e) => setContrasena(e.target.value)} minLength={8} />
              </div>
              <div className="campo">
                <label htmlFor="confirmar">Confirmar contraseña</label>
                <input id="confirmar" type="password" value={confirmar} onChange={(e) => setConfirmar(e.target.value)} minLength={8} />
              </div>
            </div>
            <div className="fila-acciones">
              <button className="btn" type="submit" disabled={guardando}>{guardando ? "Guardando..." : "Guardar cambios"}</button>
              <button className="btn secundario" type="button" onClick={() => { setEditando(false); setContrasena(""); setConfirmar(""); }}>Cancelar</button>
            </div>
          </form>
        ) : (
          <>
            <div className="grid2">
              <div className="campo"><label>Nombres</label><input type="text" value={nombres} readOnly /></div>
              <div className="campo"><label>Apellidos</label><input type="text" value={apellidos} readOnly /></div>
              <div className="campo"><label>Correo</label><input type="text" value={correo || "—"} readOnly /></div>
            </div>
            <button className="btn" style={{ marginTop: 12 }} onClick={() => setEditando(true)}>Editar perfil</button>
          </>
        )}
      </div>

      <div className="tarjeta">
        <h3>Resumen de actividad</h3>
        <div className="kpis" style={{ marginTop: 8 }}>
          <div className="kpi"><div className="valor">{total}</div><div className="etiqueta">Evaluaciones realizadas</div></div>
          <div className="kpi petroleo"><div className="valor">{ultima ? fecha(ultima.fecha) : "—"}</div><div className="etiqueta">Última evaluación</div></div>
          <div className="kpi"><div className="valor">{proxima_reevaluacion ? fecha(proxima_reevaluacion) : "—"}</div><div className="etiqueta">Próxima reevaluación</div></div>
        </div>
      </div>
    </>
  );
}