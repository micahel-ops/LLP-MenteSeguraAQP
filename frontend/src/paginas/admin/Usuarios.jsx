import { useCallback, useEffect, useState } from "react";
import { api, ETIQUETA_ROL, fecha, mensajeError, usuarioGuardado } from "../../api";

const VACIO = { rol: "ESTUDIANTE", correo: "", nombres: "", apellidos: "", contrasena: "", facultad_id: "", ciclo: "", codigo: "",
  especialidad: "", numero_colegiatura: "", facultades: [] };

function Facultades({ lista, marcadas, onCambio }) {
  return (
    <div className="campo">
      <label>Facultades que atiende</label>
      <div className="checks">
        {lista.length === 0 && <span className="nota">Primero registra una facultad.</span>}
        {lista.map((f) => (
          <label key={f.id}>
            <input type="checkbox" checked={marcadas.includes(f.id)}
                   onChange={(e) => onCambio(e.target.checked ? [...marcadas, f.id] : marcadas.filter((x) => x !== f.id))} />
            {f.nombre}
          </label>
        ))}
      </div>
    </div>
  );
}

function CamposPerfil({ rol, f, set, facultades, conCodigo }) {
  if (rol === "ESTUDIANTE") {
    return (
      <div className="grid2">
        <div className="campo">
          <label htmlFor="facultad">Facultad</label>
          <select id="facultad" value={f.facultad_id} onChange={(e) => set({ facultad_id: e.target.value })}>
            <option value="">Elige una facultad</option>
            {facultades.map((x) => <option key={x.id} value={x.id}>{x.nombre}</option>)}
          </select>
        </div>
        <div className="campo">
          <label htmlFor="ciclo">Ciclo (1 a 12)</label>
          <input id="ciclo" type="number" min="1" max="12" value={f.ciclo} onChange={(e) => set({ ciclo: e.target.value })} />
        </div>
        {conCodigo && (
          <div className="campo">
            <label htmlFor="codigo">Código (opcional)</label>
            <input id="codigo" type="text" value={f.codigo} placeholder="Se genera solo, ej. EST-0003" onChange={(e) => set({ codigo: e.target.value })} />
          </div>
        )}
      </div>
    );
  }
  if (rol === "PROFESIONAL") {
    return (
      <>
        <div className="grid2">
          <div className="campo">
            <label htmlFor="esp">Especialidad</label>
            <input id="esp" type="text" value={f.especialidad} placeholder="Psicología clínica" onChange={(e) => set({ especialidad: e.target.value })} />
          </div>
          <div className="campo">
            <label htmlFor="col">N.º de colegiatura</label>
            <input id="col" type="text" value={f.numero_colegiatura} onChange={(e) => set({ numero_colegiatura: e.target.value })} />
          </div>
        </div>
        <Facultades lista={facultades} marcadas={f.facultades} onCambio={(v) => set({ facultades: v })} />
      </>
    );
  }
  return null;
}

export default function Usuarios() {
  const yo = usuarioGuardado();
  const [lista, setLista] = useState(null);
  const [facultades, setFacultades] = useState([]);
  const [rolFiltro, setRolFiltro] = useState("");
  const [q, setQ] = useState("");
  const [creando, setCreando] = useState(false);
  const [nuevo, setNuevo] = useState(VACIO);
  const [editando, setEditando] = useState(null);
  const [ed, setEd] = useState(null);
  const [nuevaFacultad, setNuevaFacultad] = useState("");
  const [error, setError] = useState("");
  const [aviso, setAviso] = useState("");
  const [ocupado, setOcupado] = useState(false);

  const cargar = useCallback(async () => {
    try {
      const [u, f] = await Promise.all([
        api.get("/admin/usuarios", { params: { rol: rolFiltro || undefined, q: q || undefined } }),
        api.get("/admin/facultades"),
      ]);
      setLista(u.data);
      setFacultades(f.data);
    } catch (err) {
      setError(mensajeError(err, "No se pudo cargar la lista."));
    }
  }, [rolFiltro, q]);
  useEffect(() => { cargar(); }, [cargar]);

  async function ejecutar(peticion, mensajeOk, despues) {
    setError(""); setAviso(""); setOcupado(true);
    try {
      const r = await peticion();
      if (despues) despues(r);
      setAviso(mensajeOk);
      await cargar();
    } catch (err) {
      setError(mensajeError(err));
    } finally {
      setOcupado(false);
    }
  }

function crear(e) {
  e.preventDefault();

  const roles = {
    ESTUDIANTE: 1,
    PROFESIONAL: 2,
    ADMINISTRADOR: 3,
  };

  const cuerpo = {
    correo: nuevo.correo,
    nombres: nuevo.nombres,
    apellidos: nuevo.apellidos,
    contrasena: nuevo.contrasena,
    rol_id: roles[nuevo.rol],
    facultad_id: nuevo.facultad_id ? Number(nuevo.facultad_id) : null,
    ciclo: nuevo.ciclo ? Number(nuevo.ciclo) : null,
    codigo: nuevo.codigo || null,
    especialidad: nuevo.especialidad || null,
    numero_colegiatura: nuevo.numero_colegiatura || null,
    facultades: nuevo.facultades.map(Number),
  };

  ejecutar(
    () => api.post("/admin/usuarios", cuerpo),
    "Usuario creado correctamente.",
    () => {
      setNuevo(VACIO);
      setCreando(false);
    }
  );
}

function abrirEdicion(u) {
  setEditando(u);
  setEd({
    nombres: u.nombres,
    apellidos: u.apellidos,
    contrasena: "",
    facultad_id: u.facultad_id ?? "",
    ciclo: u.ciclo ?? "",
    especialidad: u.especialidad ?? "",
    numero_colegiatura: u.numero_colegiatura ?? "",
    facultades: (u.facultades || []).map((x) => x.id),
  });
  setAviso("");
  setError("");
}

function guardar(e) {
  e.preventDefault();

  const cuerpo = {
    nombres: ed.nombres,
    apellidos: ed.apellidos,
  };

  if (ed.contrasena) {
    cuerpo.contrasena = ed.contrasena;
  }

  if (editando.rol === "ESTUDIANTE") {
    if (ed.facultad_id) cuerpo.facultad_id = Number(ed.facultad_id);
    if (ed.ciclo !== "") cuerpo.ciclo = Number(ed.ciclo);
  }

  if (editando.rol === "PROFESIONAL") {
    cuerpo.especialidad = ed.especialidad;
    cuerpo.numero_colegiatura = ed.numero_colegiatura;
    cuerpo.facultades = ed.facultades;
  }

  ejecutar(
    () => api.patch(`/admin/usuarios/${editando.id}`, cuerpo),
    "Cambios guardados.",
    () => setEditando(null)
  );
}

  const cambiar = (id, cuerpo, ok) => ejecutar(() => api.patch(`/admin/usuarios/${id}`, cuerpo), ok);

  return (
    <>
      <div className="cabecera">
        <div><h1>Usuarios</h1><p className="suave">Crea y administra cuentas de estudiantes, profesionales y administradores.</p></div>
        <button className="btn" onClick={() => { setCreando(!creando); setEditando(null); setAviso(""); setError(""); }}>
          {creando ? "Cancelar" : "Nuevo usuario"}
        </button>
      </div>
      {aviso && <div className="mensaje ok" role="status">{aviso}</div>}
      {error && <div className="mensaje error" role="alert">{error}</div>}

      {creando && (
        <form className="tarjeta" style={{ marginBottom: 18 }} onSubmit={crear}>
          <h3>Nuevo usuario</h3>
          <div className="grid2">
            <div className="campo">
              <label htmlFor="nrol">Rol</label>
              <select id="nrol" value={nuevo.rol} onChange={(e) => setNuevo({ ...nuevo, rol: e.target.value })}>
                {Object.entries(ETIQUETA_ROL).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
              </select>
            </div>
            <div className="campo">
              <label htmlFor="ncorreo">Correo</label>
              <input id="ncorreo" type="email" required value={nuevo.correo} onChange={(e) => setNuevo({ ...nuevo, correo: e.target.value })} />
            </div>
            <div className="campo">
              <label htmlFor="nnom">Nombres</label>
              <input id="nnom" type="text" required value={nuevo.nombres} onChange={(e) => setNuevo({ ...nuevo, nombres: e.target.value })} />
            </div>
            <div className="campo">
              <label htmlFor="nape">Apellidos</label>
              <input id="nape" type="text" required value={nuevo.apellidos} onChange={(e) => setNuevo({ ...nuevo, apellidos: e.target.value })} />
            </div>
            <div className="campo">
              <label htmlFor="nclave">Contraseña inicial (mínimo 8 caracteres)</label>
              <input id="nclave" type="password" required minLength={8} value={nuevo.contrasena} onChange={(e) => setNuevo({ ...nuevo, contrasena: e.target.value })} />
            </div>
          </div>
          <CamposPerfil rol={nuevo.rol} f={nuevo} set={(c) => setNuevo({ ...nuevo, ...c })} facultades={facultades} conCodigo />
          <button className="btn" type="submit" disabled={ocupado}>Crear usuario</button>
        </form>
      )}

      {editando && ed && (
        <form className="tarjeta" style={{ marginBottom: 18 }} onSubmit={guardar}>
          <h3>Editar a {editando.correo}</h3>
          <div className="grid2">
            <div className="campo"><label htmlFor="enom">Nombres</label><input id="enom" type="text" required value={ed.nombres} onChange={(e) => setEd({ ...ed, nombres: e.target.value })} /></div>
            <div className="campo"><label htmlFor="eape">Apellidos</label><input id="eape" type="text" required value={ed.apellidos} onChange={(e) => setEd({ ...ed, apellidos: e.target.value })} /></div>
            <div className="campo">
              <label>Rol</label>
              <input type="text" value={ETIQUETA_ROL[editando.rol]} disabled />
            </div>
            <div className="campo"><label htmlFor="eclave">Nueva contraseña (opcional)</label><input id="eclave" type="password" minLength={8} value={ed.contrasena} onChange={(e) => setEd({ ...ed, contrasena: e.target.value })} /></div>
          </div>
          <CamposPerfil rol={editando.rol} f={ed} set={(c) => setEd({ ...ed, ...c })} facultades={facultades} />          <div className="fila-acciones">
            <button className="btn" type="submit" disabled={ocupado}>Guardar cambios</button>
            <button className="btn secundario" type="button" onClick={() => setEditando(null)}>Cancelar</button>
          </div>
        </form>
      )}

      <div className="tarjeta" style={{ marginBottom: 18 }}>
        <div className="grid2">
          <div className="campo"><label htmlFor="buscar">Buscar</label><input id="buscar" type="search" value={q} placeholder="Nombre, correo o código" onChange={(e) => setQ(e.target.value)} /></div>
          <div className="campo">
            <label htmlFor="filtrorol">Rol</label>
            <select id="filtrorol" value={rolFiltro} onChange={(e) => setRolFiltro(e.target.value)}>
              <option value="">Todos</option>
              {Object.entries(ETIQUETA_ROL).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
            </select>
          </div>
        </div>
        {lista && lista.length === 0 && <p className="vacio">No hay usuarios con ese filtro.</p>}
        {lista && lista.length > 0 && (
          <div className="tabla-contenedor">
            <table>
              <thead><tr><th>Usuario</th><th>Rol</th><th>Datos</th><th>Estado</th><th>Último acceso</th><th>Acciones</th></tr></thead>
              <tbody>
                {lista.map((u) => (
                  <tr key={u.id}>
                    <td><strong>{u.nombres} {u.apellidos}</strong><div className="nota">{u.correo}</div></td>
                    <td>{ETIQUETA_ROL[u.rol]}</td>
                    <td>
                      {u.codigo && <>{u.codigo} · {u.facultad} · ciclo {u.ciclo ?? "—"}{u.consentimiento === false && <div className="nota">Sin consentimiento aún</div>}</>}
                      {u.especialidad !== null && u.rol === "PROFESIONAL" && <>{u.especialidad || "Sin especialidad"}<div className="nota">{u.facultades.map((f) => f.nombre).join(", ") || "Sin facultades asignadas"}</div></>}
                    </td>
                    <td>
                      <span className={`chip ${u.activo ? "ok" : "alto"}`}>{u.activo ? "Activo" : "Inactivo"}</span>
                      {u.bloqueado && <div><span className="chip aviso">Bloqueado</span></div>}
                    </td>
                    <td>{fecha(u.ultimo_acceso, true)}</td>
                    <td>
                      <div className="fila-acciones" style={{ marginTop: 0 }}>
                        <button className="btn secundario chico" onClick={() => abrirEdicion(u)}>Editar</button>
                        {u.id !== yo.id && (
                          <button className="btn secundario chico" disabled={ocupado}
                                  onClick={() => cambiar(u.id, { activo: !u.activo }, u.activo ? "Usuario desactivado." : "Usuario activado.")}>
                            {u.activo ? "Desactivar" : "Activar"}
                          </button>
                        )}
                        {u.bloqueado && <button className="btn chico" disabled={ocupado} onClick={() => cambiar(u.id, { desbloquear: true }, "Cuenta desbloqueada.")}>Desbloquear</button>}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <div className="tarjeta">
        <h3>Facultades</h3>
        <div style={{ marginBottom: 12 }}>{facultades.map((f) => <span key={f.id} className="chip" style={{ marginRight: 6, marginBottom: 6 }}>{f.nombre}</span>)}</div>
        <form className="fila-acciones" onSubmit={(e) => { e.preventDefault(); ejecutar(() => api.post("/admin/facultades", { nombre: nuevaFacultad }), "Facultad registrada.", () => setNuevaFacultad("")); }}>
          <div style={{ flex: 1, minWidth: 220 }}>
            <label htmlFor="nfac" className="nota">Nueva facultad</label>
            <input id="nfac" type="text" value={nuevaFacultad} placeholder="Ej. Ingeniería de Sistemas" onChange={(e) => setNuevaFacultad(e.target.value)} />
          </div>
          <button className="btn petroleo" type="submit" disabled={ocupado || !nuevaFacultad.trim()} style={{ alignSelf: "flex-end" }}>Agregar</button>
        </form>
      </div>
    </>
  );
}
