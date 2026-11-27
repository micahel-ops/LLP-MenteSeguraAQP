import { useCallback, useEffect, useState } from "react";
import { api, fecha, mensajeError } from "../../api";

export default function ModeloNLP() {
  const [modelos, setModelos] = useState(null);
  const [error, setError] = useState("");
  const [aviso, setAviso] = useState("");
  const [mostrandoModal, setMostrandoModal] = useState(false);
  const [editando, setEditando] = useState(null);

  const [version, setVersion] = useState("");
  const [estado, setEstado] = useState("VIGENTE");
  const [motivoDecision, setMotivoDecision] = useState("");
  const [guardando, setGuardando] = useState(false);

  const cargar = useCallback(async () => {
    try {
      const r = await api.get("/admin/modelo-nlp");
      setModelos(r.data);
    } catch (err) {
      setError(mensajeError(err, "No se pudieron cargar las versiones del modelo NLP."));
    }
  }, []);

  useEffect(() => { cargar(); }, [cargar]);

  function abrirNuevo() {
    setEditando(null);
    setVersion("");
    setEstado("VIGENTE");
    setMotivoDecision("");
    setMostrandoModal(true);
  }

  function abrirEditar(m) {
    setEditando(m);
    setVersion(m.version || "");
    setEstado(m.estado || "VIGENTE");
    setMotivoDecision(m.motivo_decision || "");
    setMostrandoModal(true);
  }

  async function guardar(e) {
    e.preventDefault();
    setError(""); setAviso(""); setGuardando(true);
    try {
      if (editando) {
        await api.patch(`/admin/modelo-nlp/${editando.id}`, {
          version: version.trim(),
          estado,
          motivo_decision: motivoDecision.trim() || null
        });
        setAviso("Modelo NLP actualizado correctamente.");
      } else {
        await api.post("/admin/modelo-nlp", {
          version: version.trim(),
          estado,
          motivo_decision: motivoDecision.trim() || null
        });
        setAviso("Nuevo modelo NLP registrado correctamente.");
      }
      setMostrandoModal(false);
      await cargar();
    } catch (err) {
      setError(mensajeError(err));
    } finally {
      setGuardando(false);
    }
  }

  async function eliminar(m) {
    if (!window.confirm(`¿Seguro que deseas eliminar la versión "${m.version}"?`)) return;
    setError(""); setAviso("");
    try {
      await api.delete(`/admin/modelo-nlp/${m.id}`);
      setAviso("Modelo NLP eliminado.");
      await cargar();
    } catch (err) {
      setError(mensajeError(err));
    }
  }

  if (!modelos) {
    return <>{error ? <div className="mensaje error" role="alert">{error}</div> : <p className="suave">Cargando versiones del modelo NLP...</p>}</>;
  }

  return (
    <>
      <div className="cabecera">
        <div><h1>Control de versiones del modelo NLP</h1><p className="suave">Gestión de pesos, heurísticas y versiones del analizador de lenguaje natural.</p></div>
        <button className="btn" onClick={abrirNuevo}>+ Registrar versión</button>
      </div>

      {aviso && <div className="mensaje ok" role="status">{aviso}</div>}
      {error && <div className="mensaje error" role="alert">{error}</div>}

      <div className="tarjeta">
        {modelos.length === 0 && <p className="vacio">No hay versiones registradas.</p>}
        {modelos.length > 0 && (
          <div className="tabla-contenedor">
            <table>
              <thead>
                <tr>
                  <th>Versión</th>
                  <th>Estado</th>
                  <th>Publicado en</th>
                  <th>Motivo de decisión</th>
                  <th>Acciones</th>
                </tr>
              </thead>
              <tbody>
                {modelos.map((m) => (
                  <tr key={m.id}>
                    <td><strong>{m.version}</strong></td>
                    <td><span className={`chip ${m.estado === "VIGENTE" ? "ok" : "suave"}`}>{m.estado}</span></td>
                    <td>{m.publicado_en ? fecha(m.publicado_en) : "—"}</td>
                    <td>{m.motivo_decision || "—"}</td>
                    <td>
                      <div className="acciones-inline">
                        <button className="enlace" onClick={() => abrirEditar(m)}>Editar</button>
                        <button className="enlace terracota" onClick={() => eliminar(m)}>Eliminar</button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {mostrandoModal && (
        <div className="modal-overlay">
          <div className="tarjeta modal-contenido" style={{ maxWidth: 500 }}>
            <h3>{editando ? "Editar modelo NLP" : "Registrar nuevo modelo NLP"}</h3>
            <form onSubmit={guardar}>
              <div className="campo" style={{ marginBottom: 12 }}>
                <label htmlFor="m-version">Versión *</label>
                <input id="m-version" type="text" required placeholder="Ej: heuristico-v2.0 o bert-aqp-v1" value={version} onChange={(e) => setVersion(e.target.value)} />
              </div>

              <div className="campo" style={{ marginBottom: 12 }}>
                <label htmlFor="m-estado">Estado *</label>
                <select id="m-estado" value={estado} onChange={(e) => setEstado(e.target.value)}>
                  <option value="VIGENTE">VIGENTE (En uso)</option>
                  <option value="RETIRADA">RETIRADA (Histórico)</option>
                </select>
                <span className="nota">Al marcar como VIGENTE, el modelo anterior pasará a estado RETIRADA automáticamente.</span>
              </div>

              <div className="campo" style={{ marginBottom: 16 }}>
                <label htmlFor="m-motivo">Motivo de decisión / Cambios</label>
                <textarea id="m-motivo" rows={3} placeholder="Describa los cambios, mejoras en el diccionario o pesos actualizados..." value={motivoDecision} onChange={(e) => setMotivoDecision(e.target.value)} />
              </div>

              <div className="fila-acciones">
                <button className="btn" type="submit" disabled={guardando}>{guardando ? "Guardando..." : "Guardar"}</button>
                <button className="btn secundario" type="button" onClick={() => setMostrandoModal(false)}>Cancelar</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  );
}
