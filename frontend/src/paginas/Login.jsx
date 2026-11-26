import { useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import { api, guardarSesion, mensajeError, rutaPorRol, usuarioGuardado } from "../api";
import Logo from "../componentes/Logo";

const DEMO = [
  { rol: "Estudiante", correo: "estudiante@demo.pe" },
  { rol: "Profesional", correo: "profesional@demo.pe" },
  { rol: "Administrador", correo: "admin@demo.pe" },
];

export default function Login() {
  const [correo, setCorreo] = useState("");
  const [contrasena, setContrasena] = useState("");
  const [error, setError] = useState("");
  const [cargando, setCargando] = useState(false);
  const navigate = useNavigate();

  const sesion = usuarioGuardado();
  if (sesion && localStorage.getItem("token")) return <Navigate to={rutaPorRol[sesion.rol]} replace />;

  async function enviar(e) {
    e.preventDefault();
    setError("");
    setCargando(true);
    try {
      const { data } = await api.post("/login", { correo, contrasena });
      guardarSesion(data);
      navigate(rutaPorRol[data.usuario.rol]);
    } catch (err) {
      setError(mensajeError(err, "No se pudo iniciar sesión."));
    } finally {
      setCargando(false);
    }
  }

  return (
    <div className="login">
      <section className="login-izq">
        <Logo tono="claro" tam={44} />
        <div>
          <h1>Cuidar tu mente también es parte de estudiar</h1>
          <p>
            Mente Sana AQP ayuda a detectar a tiempo señales de malestar en estudiantes universitarios de
            Arequipa y a coordinar el apoyo con profesionales de salud mental.
          </p>
        </div>
        <p className="nota" style={{ color: "#CFE0E2" }}>¿Necesitas ayuda ahora? Llama a la Línea 113 (Minsa).</p>
      </section>

      <section className="login-der">
        <form className="login-form" onSubmit={enviar}>
          <h2>Iniciar sesión</h2>
          <p className="suave">Ingresa con tu cuenta institucional.</p>

          <div className="campo">
            <label htmlFor="correo">Correo institucional</label>
            <input id="correo" type="email" value={correo} placeholder="nombre@universidad.edu.pe"
                   onChange={(e) => setCorreo(e.target.value)} required autoComplete="username" />
          </div>
          <div className="campo">
            <label htmlFor="clave">Contraseña</label>
            <input id="clave" type="password" value={contrasena} placeholder="••••••••••"
                   onChange={(e) => setContrasena(e.target.value)} required autoComplete="current-password" />
          </div>

          {error && <div className="mensaje error" role="alert">{error}</div>}
          <button className="btn" type="submit" disabled={cargando} style={{ width: "100%" }}>
            {cargando ? "Ingresando..." : "Ingresar"}
          </button>
          <p className="nota" style={{ textAlign: "center", marginTop: 12 }}>
            Tus datos son confidenciales y se usan solo con fines de orientación y prevención.
          </p>

          {import.meta.env.DEV && (
            <div className="demo">
              <strong>Cuentas de demostración</strong>
              <p className="nota">Solo en desarrollo. Clave de todas: Demo2026!</p>
              <div className="fila-acciones">
                {DEMO.map((d) => (
                  <button key={d.correo} type="button" className="btn secundario chico"
                          onClick={() => { setCorreo(d.correo); setContrasena("Demo2026!"); setError(""); }}>
                    {d.rol}
                  </button>
                ))}
              </div>
            </div>
          )}
        </form>
      </section>
    </div>
  );
}
