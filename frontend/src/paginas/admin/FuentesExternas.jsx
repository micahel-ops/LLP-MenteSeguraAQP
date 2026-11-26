
import { useCallback, useEffect, useState } from "react";
import { api, mensajeError } from "../../api";

export default function FuentesExternas() {
  const [fuentes, setFuentes] = useState(null);
  const [error, setError] = useState("");
  const [aviso, setAviso] = useState("");
  const [mostrandoModal, setMostrandoModal] = useState(false);
  const [editando, setEditando] = useState(null);
  const [guardando, setGuardando] = useState(false);

  const [nombre, setNombre] = useState("");
  const [organismoTipo, setOrganismoTipo] = useState("");
  const [tipoAcceso, setTipoAcceso] = useState("");
  const [clasificacion, setClasificacion] = useState("");
  const [url, setUrl] = useState("");
  const [frecuenciaDias, setFrecuenciaDias] = useState(7);
  const [activa, setActiva] = useState(true);

  const cargar = useCallback(async () => {
    try {
      const r = await api.get("/admin/fuentes-externas");
      setFuentes(r.data);
      setError("");
    } catch (err) {
      setError(mensajeError(err, "No se pudieron cargar las fuentes externas."));
    }
  }, []);

  useEffect(() => {
    cargar();
  }, [cargar]);

  function limpiarFormulario() {
    setNombre("");
    setOrganismoTipo("");
    setTipoAcceso("");
    setClasificacion("");
    setUrl("");
    setFrecuenciaDias(7);
    setActiva(true);
  }

  function abrirNuevo() {
    setEditando(null);
    limpiarFormulario();
    setMostrandoModal(true);
  }

  function abrirEditar(f) {
    setEditando(f);
    setNombre(f.nombre || "");
    setOrganismoTipo(f.organismo_tipo || "");
    setTipoAcceso(f.tipo_acceso || "");
    setClasificacion(f.clasificacion || "");
    setUrl(f.url || "");
    setFrecuenciaDias(f.frecuencia_dias || 7);
    setActiva(Boolean(f.activa));
    setMostrandoModal(true);
  }

  async function guardar(e) {
    e.preventDefault();
    setError("");
    setAviso("");
    setGuardando(true);

    const datos = {
      nombre: nombre.trim(),
      organismo_tipo: organismoTipo,
      tipo_acceso: tipoAcceso,
      clasificacion: clasificacion,
      url: url.trim(),
      frecuencia_dias: Number(frecuenciaDias),
      activa
    };

    try {
      if (editando) {
        await api.patch(`/admin/fuentes-externas/${editando.id}`, datos);
        setAviso("Fuente externa actualizada correctamente.");
      } else {
        await api.post("/admin/fuentes-externas", datos);
        setAviso("Fuente externa creada correctamente.");
      }

      setMostrandoModal(false);
      await cargar();
    } catch (err) {
      setError(mensajeError(err));
    } finally {
      setGuardando(false);
    }
  }

  async function eliminar(f) {
    if (!window.confirm(`¿Seguro que deseas eliminar la fuente "${f.nombre}"?`)) {
      return;
    }

    setError("");
    setAviso("");

    try {
      await api.delete(`/admin/fuentes-externas/${f.id}`);
      setAviso("Fuente externa eliminada.");
      await cargar();
    } catch (err) {
      setError(mensajeError(err));
    }
  }

  if (!fuentes) {
    return (
      <>
        {error
          ? <div className="mensaje error" role="alert">{error}</div>
          : <p className="suave">Cargando fuentes externas...</p>}
      </>
    );
  }

  return (
    <>
      <div className="cabecera">
        <div>
          <h1>Fuentes externas</h1>
          <p className="suave">
            Administración de orígenes de datos externos e integración de información.
          </p>
        </div>
        <button className="btn" onClick={abrirNuevo}>
          + Nueva fuente
        </button>
      </div>

      {aviso && <div className="mensaje ok" role="status">{aviso}</div>}
      {error && <div className="mensaje error" role="alert">{error}</div>}

      <div className="tarjeta">
        {fuentes.length === 0 && (
          <p className="vacio">No hay fuentes externas registradas.</p>
        )}

        {fuentes.length > 0 && (
          <div className="tabla-contenedor">
            <table>
              <thead>
                <tr>
                  <th>Nombre</th>
                  <th>Organismo</th>
                  <th>Tipo de acceso</th>
                  <th>Clasificación</th>
                  <th>URL</th>
                  <th>Frecuencia</th>
                  <th>Estado</th>
                  <th>Acciones</th>
                </tr>
              </thead>

              <tbody>
                {fuentes.map((f) => (
                  <tr key={f.id}>
                    <td><strong>{f.nombre}</strong></td>
                    <td>{f.organismo_tipo}</td>
                    <td>{f.tipo_acceso}</td>
                    <td>{f.clasificacion}</td>
                    <td>
                      {f.url
                        ? <a href={f.url} target="_blank" rel="noreferrer" className="enlace">{f.url}</a>
                        : "—"}
                    </td>
                    <td>{f.frecuencia_dias} días</td>
                    <td>
                      <span className={`chip ${f.activa ? "ok" : "suave"}`}>
                        {f.activa ? "Activa" : "Inactiva"}
                      </span>
                    </td>
                    <td>
                      <div className="acciones-inline">
                        <button className="enlace" onClick={() => abrirEditar(f)}>
                          Editar
                        </button>
                        <button className="enlace terracota" onClick={() => eliminar(f)}>
                          Eliminar
                        </button>
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
          <div className="tarjeta modal-contenido" style={{ maxWidth: 550 }}>
            <h3>{editando ? "Editar fuente externa" : "Nueva fuente externa"}</h3>

            <form onSubmit={guardar}>
              <div className="campo" style={{ marginBottom: 12 }}>
                <label htmlFor="f-nombre">Nombre *</label>
                <input
                  id="f-nombre"
                  type="text"
                  maxLength={120}
                  required
                  value={nombre}
                  onChange={(e) => setNombre(e.target.value)}
                />
              </div>


<div className="campo" style={{ marginBottom: 12 }}>
  <label htmlFor="f-organismo">Organismo tipo *</label>
  <select
    id="f-organismo"
    required
    value={organismoTipo}
    onChange={(e) => setOrganismoTipo(e.target.value)}
  >
    <option value="">Seleccionar organismo</option>
    <option value="ESTADO">ESTADO</option>
    <option value="ONG">ONG</option>
    <option value="INTERNACIONAL">INTERNACIONAL</option>
  </select>
</div>

<div className="campo" style={{ marginBottom: 12 }}>
  <label htmlFor="f-acceso">Tipo de acceso *</label>
  <select
    id="f-acceso"
    required
    value={tipoAcceso}
    onChange={(e) => setTipoAcceso(e.target.value)}
  >
    <option value="">Seleccionar acceso</option>
    <option value="API">API</option>
    <option value="CSV">CSV</option>
    <option value="WEB">WEB</option>
    <option value="PDF">PDF</option>
  </select>
</div>

<div className="campo" style={{ marginBottom: 12 }}>
  <label htmlFor="f-clasificacion">Clasificación *</label>
  <select
    id="f-clasificacion"
    required
    value={clasificacion}
    onChange={(e) => setClasificacion(e.target.value)}
  >
    <option value="">Seleccionar clasificación</option>
    <option value="RELACIONAL">RELACIONAL</option>
    <option value="NO_RELACIONAL">NO_RELACIONAL</option>
  </select>
</div>


              <div className="campo" style={{ marginBottom: 12 }}>
                <label htmlFor="f-acceso">Tipo de acceso *</label>
                <input
                  id="f-acceso"
                  type="text"
                  maxLength={5}
                  required
                  value={tipoAcceso}
                  onChange={(e) => setTipoAcceso(e.target.value)}
                />
              </div>

              <div className="campo" style={{ marginBottom: 12 }}>
                <label htmlFor="f-clasificacion">Clasificación *</label>
                <input
                  id="f-clasificacion"
                  type="text"
                  maxLength={13}
                  required
                  value={clasificacion}
                  onChange={(e) => setClasificacion(e.target.value)}
                />
              </div>

              <div className="campo" style={{ marginBottom: 12 }}>
                <label htmlFor="f-url">URL *</label>
                <input
                  id="f-url"
                  type="url"
                  maxLength={400}
                  required
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                />
              </div>

              <div className="campo" style={{ marginBottom: 12 }}>
                <label htmlFor="f-frecuencia">Frecuencia de actualización (días) *</label>
                <input
                  id="f-frecuencia"
                  type="number"
                  min="1"
                  max="65535"
                  required
                  value={frecuenciaDias}
                  onChange={(e) => setFrecuenciaDias(e.target.value)}
                />
              </div>

              <div className="campo" style={{ marginBottom: 16 }}>
                <label style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  <input
                    type="checkbox"
                    checked={activa}
                    onChange={(e) => setActiva(e.target.checked)}
                  />
                  Fuente activa
                </label>
              </div>

              <div className="fila-acciones">
                <button className="btn" type="submit" disabled={guardando}>
                  {guardando ? "Guardando..." : "Guardar"}
                </button>
                <button
                  className="btn secundario"
                  type="button"
                  onClick={() => setMostrandoModal(false)}
                >
                  Cancelar
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  );
}
