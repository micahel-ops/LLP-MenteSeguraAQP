import { useEffect } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import { api, cerrarSesion, ETIQUETA_ROL, usuarioGuardado } from "../api";
import Logo from "./Logo";

export default function Layout({ menu, children }) {
  const navigate = useNavigate();
  const u = usuarioGuardado();

  // Comprueba con el backend que la sesión sigue siendo válida
  useEffect(() => {
    api.get("/yo").catch(() => {
      cerrarSesion();
      navigate("/login");
    });
  }, [navigate]);

  function salir() {
    cerrarSesion();
    navigate("/login");
  }

  return (
    <div className="app">
      <aside className="lateral">
        <Logo tono="claro" />
        <nav aria-label="Menú principal" style={{ display: "contents" }}>
          {menu.map((m) =>
            m.ruta ? (
              <NavLink key={m.texto} to={m.ruta} end={m.exacta !== false}
                       className={({ isActive }) => (isActive ? "menu-item activo" : "menu-item")}>
                {m.texto}
              </NavLink>
            ) : (
              <span key={m.texto} className="menu-item apagado" aria-disabled="true">{m.texto}</span>
            )
          )}
        </nav>
        <div className="usuario">
          <strong>{u.nombres} {u.apellidos}</strong>
          <span className="rol">{ETIQUETA_ROL[u.rol]}</span>
          <button className="salir" onClick={salir}>Cerrar sesión</button>
        </div>
      </aside>
      <main className="contenido"><div className="pagina">{children}</div></main>
    </div>
  );
}
