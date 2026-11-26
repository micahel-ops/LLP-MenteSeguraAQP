
import { useEffect, useState } from "react";
import { api, ETIQUETA_ROL, mensajeError } from "../../api";
import { Barras, Columnas } from "../../componentes/Graficos";

function mesCorto(m) {
  const nombres = [
    "ene", "feb", "mar", "abr", "may", "jun",
    "jul", "ago", "sep", "oct", "nov", "dic"
  ];

  return nombres[Number(m.slice(5, 7)) - 1];
}

export default function Panel() {
  const [d, setD] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .get("/admin/panel")
      .then((r) => setD(r.data))
      .catch((err) =>
        setError(mensajeError(err, "No se pudo cargar el panel."))
      );
  }, []);

  if (!d) {
    return (
      <>
        {error ? (
          <div className="mensaje error" role="alert">
            {error}
          </div>
        ) : (
          <p className="suave">Cargando...</p>
        )}
      </>
    );
  }

  const activos = d.usuarios.reduce((s, u) => s + u.activos, 0);

  const abiertos =
    d.alertas.nuevas +
    d.alertas.en_revision +
    d.alertas.sin_asignar +
    d.alertas.por_etapa +
    d.alertas.atendidas +
    d.alertas.descartadas;

  const n = d.evaluaciones.por_nivel;

  return (
    <>
      <div className="cabecera">
        <div>
          <h1>Panel de administración</h1>
          <p className="suave">Resumen general de la plataforma.</p>
        </div>
      </div>

      <div className="kpis">
        <div className="kpi">
          <div className="valor">{activos}</div>
          <div className="etiqueta">Usuarios activos</div>
        </div>

        <div className="kpi petroleo">
          <div className="valor">{d.evaluaciones.total}</div>
          <div className="etiqueta">Evaluaciones registradas</div>
        </div>

        <div className="kpi terracota">
          <div className="valor">{abiertos}</div>
          <div className="etiqueta">Total de casos</div>
        </div>

        <div className="kpi">
          <div className="valor">{d.alertas.sin_asignar}</div>
          <div className="etiqueta">Casos sin asignar</div>
        </div>
      </div>

      <div className="cols" style={{ marginBottom: 18 }}>
        <div className="tarjeta">
          <h3>Evaluaciones de los últimos 6 meses</h3>
          <Columnas
            items={d.evaluaciones.por_mes.map((m) => ({
              etiqueta: mesCorto(m.mes),
              valor: m.total
            }))}
          />
        </div>

        <div className="tarjeta">
          <h3>Usuarios por rol</h3>
          <table>
            <thead>
              <tr>
                <th>Rol</th>
                <th>Activos</th>
                <th>Total</th>
              </tr>
            </thead>
            <tbody>
              {d.usuarios.map((u) => (
                <tr key={u.rol}>
                  <td>{ETIQUETA_ROL[u.rol]}</td>
                  <td>{u.activos}</td>
                  <td>{u.total}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="cols" style={{ marginBottom: 18 }}>
        <div className="tarjeta">
          <h3>Flujo de casos por etapa</h3>
          <Barras
            items={[
              {
                etiqueta: "Nueva",
                valor: d.alertas.nuevas,
                color: "var(--terracota)"
              },
              {
                etiqueta: "En revisión",
                valor: d.alertas.en_revision,
                color: "var(--petroleo)"
              },
              {
                etiqueta: "Por etapa",
                valor: d.alertas.por_etapa,
                color: "var(--cobre)"
              },
              {
                etiqueta: "Atendidas",
                valor: d.alertas.atendidas,
                color: "var(--salvia)"
              },
              {
                etiqueta: "Descartadas",
                valor: d.alertas.descartadas,
                color: "var(--gris)"
              }
            ]}
          />
        </div>

        <div className="tarjeta">
          <h3>Nivel de las evaluaciones</h3>
          <Barras
            items={[
              {
                etiqueta: "Bajo",
                valor: n.BAJO,
                color: "var(--salvia)"
              },
              {
                etiqueta: "Medio",
                valor: n.MEDIO,
                color: "var(--cobre)"
              },
              {
                etiqueta: "Alto",
                valor: n.ALTO,
                color: "var(--ladrillo)"
              }
            ]}
          />
        </div>
      </div>

      <div className="tarjeta">
        <h3>Por facultad</h3>

        {d.facultades.length === 0 && (
          <p className="vacio">Aún no hay facultades registradas.</p>
        )}

        {d.facultades.length > 0 && (
          <div className="tabla-contenedor">
            <table>
              <thead>
                <tr>
                  <th>Facultad</th>
                  <th>Evaluaciones</th>
                  <th>Alertas</th>
                </tr>
              </thead>
              <tbody>
                {d.facultades.map((f) => (
                  <tr key={f.facultad}>
                    <td>{f.facultad}</td>
                    <td>{f.evaluaciones}</td>
                    <td>{f.alertas}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Nueva sección: Resumen de actividades */}
      <div
        className="tarjeta"
        style={{ marginTop: 18, marginBottom: 18 }}
      >
        <h3>Actividades recientes</h3>

        {d.actividad && d.actividad.length > 0 ? (
          <div style={{ maxHeight: 200, overflowY: "auto" }}>
            {d.actividad.slice(0, 10).map((a) => (
              <div
                key={a.id}
                style={{
                  padding: "4px 0",
                  borderBottom: "1px solid #eee"
                }}
              >
                <span style={{ fontWeight: "bold" }}>
                  {a.accion}
                </span>{" "}
                por {a.nombres} {a.apellidos} - {a.fecha}
              </div>
            ))}
          </div>
        ) : (
          <p>No hay actividades registradas.</p>
        )}
      </div>
    </>
  );
}
