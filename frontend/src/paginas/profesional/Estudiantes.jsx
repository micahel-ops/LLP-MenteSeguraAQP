import { useCallback, useEffect, useState } from "react";
import { api, CLASE_NIVEL, ESTADO_ALERTA, fecha, mensajeError, NIVEL_PROFESIONAL } from "../../api";

export default function Estudiantes() {
  const [estudiantes, setEstudiantes] = useState(null);
  const [filtro, setFiltro] = useState("");
  const [facultadFiltro, setFacultadFiltro] = useState("");
  const [facultades, setFacultades] = useState([]);
  const [error, setError] = useState("");
  const [verDetalle, setVerDetalle] = useState(null);

  const cargar = useCallback(async () => {
    try {
      const r1 = await api.get("/profesional/estudiantes", { params: { q: filtro || undefined, facultad: facultadFiltro || undefined } });
      setEstudiantes(r1.data);
    } catch (err) {
      setError(mensajeError(err, "No se pudo cargar la lista de estudiantes."));
    }
  }, [filtro, facultadFiltro]);

  useEffect(() => { cargar(); }, [cargar]);

  if (!estudiantes) {
    return <>{error ? <div className="mensaje error" role="alert">{error}</div> : <p className="suave">Cargando estudiantes...</p>}</>;
  }

  return (
    <>
      <div className="cabecera">
        <div><h1>Mis estudiantes</h1><p className="suave">Lista de estudiantes asignados a tu facultad.</p></div>
      </div>

      {error && <div className="mensaje error" role="alert">{error}</div>}

      <div className="tarjeta" style={{ marginBottom: 18 }}>
        <h3>Filtros</h3>
        <div className="grid2" style={{ marginBottom: 12 }}>
          <div className="campo">
            <label htmlFor="buscar">Buscar</label>
            <input id="buscar" type="search" value={filtro} placeholder="Nombre, código o correo" onChange={(e) => setFiltro(e.target.value)} />
          </div>
          <div className="campo">
            <label htmlFor="facultad">Facultad</label>
            <select id="facultad" value={facultadFiltro} onChange={(e) => setFacultadFiltro(e.target.value)}>
              <option value="">Todas</option>
              {facultades.map((f) => <option key={f.id} value={f.id}>{f.nombre}</option>)}
            </select>
          </div>
        </div>
      </div>

      <div className="tarjeta">
        {estudiantes.length === 0 && <p className="vacio">No hay estudiantes con ese filtro.</p>}
        {estudiantes.length > 0 && (
          <div className="tabla-contenedor">
            <table>
              <thead>
                <tr><th>Estudiante</th><th>Facultad</th><th>Ciclo</th><th>Última evaluación</th><th>Nivel</th><th>Casos</th><th></th></tr>
              </thead>
              <tbody>
                {estudiantes.map((e) => (
                  <tr key={e.id}>
                    <td><strong>{e.nombres} {e.apellidos}</strong><div className="nota">{e.correo}</div></td>
                    <td>{e.facultad}</td>
                    <td>{e.ciclo ?? "—"}</td>
                    <td>{e.ultima_fecha ? fecha(e.ultima_fecha) : "—"}</td>
                    <td>{e.ultima_nivel ? <span className={`chip ${CLASE_NIVEL[e.ultima_nivel]}`}>{NIVEL_PROFESIONAL[e.ultima_nivel]}</span> : "—"}</td>
                    <td>
                      {e.casos_nuevos > 0 && <span className="chip alto">Nuevos: {e.casos_nuevos}</span>}
                      {e.casos_en_revision > 0 && <span className="chip aviso">En revisión: {e.casos_en_revision}</span>}
                      {e.casos_cerrados > 0 && <span className="chip ok">Cerrados: {e.casos_cerrados}</span>}
                    </td>
                    <td>
                      <button className="enlace" onClick={() => setVerDetalle(e)}>Ver detalle</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {verDetalle && (
        <div className="tarjeta" style={{ marginTop: 18 }}>
          <h3>Detalle de {verDetalle.nombres} {verDetalle.apellidos}</h3>
          <div className="grid2" style={{ marginBottom: 12 }}>
            <div className="campo"><label>Código</label><input type="text" value={verDetalle.codigo || "—"} readOnly /></div>
            <div className="campo"><label>Facultad</label><input type="text" value={verDetalle.facultad} readOnly /></div>
            <div className="campo"><label>Ciclo</label><input type="text" value={verDetalle.ciclo ? String(verDetalle.ciclo) : "—"} readOnly /></div>
            <div className="campo"><label>Correo</label><input type="text" value={verDetalle.correo} readOnly /></div>
          </div>

          <div className="tarjeta" style={{ marginTop: 12 }}>
            <h4>Últimas evaluaciones</h4>
            {verDetalle.evaluaciones.length === 0 ? (
              <p className="vacio">Sin evaluaciones registradas.</p>
            ) : (
              <div className="tabla-contenedor">
                <table>
                  <thead><tr><th>Fecha</th><th>Instrumento</th><th>Puntaje</th><th>Categoría</th><th>Nivel</th></tr></thead>
                  <tbody>
                    {verDetalle.evaluaciones.map((ev) => (
                      <tr key={ev.id}>
                        <td>{fecha(ev.fecha)}</td>
                        <td>{ev.instrumento}</td>
                        <td>{ev.puntaje}</td>
                        <td>{ev.categoria}</td>
                        <td><span className={`chip ${CLASE_NIVEL[ev.nivel]}`}>{NIVEL_PROFESIONAL[ev.nivel]}</span></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          <div className="tarjeta" style={{ marginTop: 12 }}>
            <h4>Casos activos</h4>
            {verDetalle.alertas.length === 0 ? (
              <p className="vacio">No tiene casos activos.</p>
            ) : (
              <div className="tabla-contenedor">
                <table>
                  <thead><tr><th>Prioridad</th><th>Motivo</th><th>Estado</th><th>Etapa</th></tr></thead>
                  <tbody>
                    {verDetalle.alertas.map((a) => (
                      <tr key={a.id}>
                        <td><span className="chip terracota">{a.prioridad}</span></td>
                        <td>{a.motivo}</td>
                        <td><span className={`chip ${a.estado === "ATENDIDA" || a.estado === "DESCARTADA" ? "petroleo" : "aviso"}`}>{ESTADO_ALERTA[a.estado]}</span></td>
                        <td>{a.etapa_nombre}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          <button className="btn secundario" style={{ marginTop: 12 }} onClick={() => setVerDetalle(null)}>Cerrar</button>
        </div>
      )}
    </>
  );
}