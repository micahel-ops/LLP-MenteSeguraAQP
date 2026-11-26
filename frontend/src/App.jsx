import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import Layout from "./componentes/Layout";
import Login from "./paginas/Login";
import EstudianteInicio from "./paginas/estudiante/Inicio";
import Evaluacion from "./paginas/estudiante/Evaluacion";
import MisResultados from "./paginas/estudiante/MisResultados";
import Recomendaciones from "./paginas/estudiante/Recomendaciones";
import MiPerfil from "./paginas/estudiante/MiPerfil";
import Bandeja from "./paginas/profesional/Bandeja";
import Caso from "./paginas/profesional/Caso";
import Estudiantes from "./paginas/profesional/Estudiantes";
import Seguimientos from "./paginas/profesional/Seguimientos";
import Reportes from "./paginas/profesional/Reportes";
import AdminPanel from "./paginas/admin/Panel";
import Usuarios from "./paginas/admin/Usuarios";
import Casos from "./paginas/admin/Casos";
import Actividad from "./paginas/admin/Actividad";
import FuentesExternas from "./paginas/admin/FuentesExternas";
import ModeloNLP from "./paginas/admin/ModeloNLP";
import { rutaPorRol, usuarioGuardado } from "./api";

// Solo deja entrar a quien tiene sesión y el rol correcto
function Protegida({ rol, menu, children }) {
  const u = usuarioGuardado();
  if (!localStorage.getItem("token") || !u) return <Navigate to="/login" replace />;
  if (u.rol !== rol) return <Navigate to={rutaPorRol[u.rol]} replace />;
  return <Layout menu={menu}>{children}</Layout>;
}

const MENU_ESTUDIANTE = [
  { texto: "Inicio", ruta: "/estudiante" },
  { texto: "Nueva evaluación", ruta: "/estudiante/evaluar" },
  { texto: "Mis resultados", ruta: "/estudiante/resultados" },
  { texto: "Recomendaciones", ruta: "/estudiante/recomendaciones" },
  { texto: "Mi perfil", ruta: "/estudiante/perfil" },
];
const MENU_PROFESIONAL = [
  { texto: "Bandeja de casos", ruta: "/profesional" },
  { texto: "Mis estudiantes", ruta: "/profesional/estudiantes" },
  { texto: "Seguimientos", ruta: "/profesional/seguimientos" },
  { texto: "Reportes", ruta: "/profesional/reportes" },
];
const MENU_ADMIN = [
  { texto: "Panel general", ruta: "/admin" },
  { texto: "Usuarios", ruta: "/admin/usuarios" },
  { texto: "Casos", ruta: "/admin/casos" },
  { texto: "Actividad", ruta: "/admin/actividad" },
  { texto: "Fuentes externas", ruta: "/admin/fuentes-externas" },
  { texto: "Modelo NLP", ruta: "/admin/modelo-nlp" },
];

export default function App() {
  const E = (el) => <Protegida rol="ESTUDIANTE" menu={MENU_ESTUDIANTE}>{el}</Protegida>;
  const P = (el) => <Protegida rol="PROFESIONAL" menu={MENU_PROFESIONAL}>{el}</Protegida>;
  const A = (el) => <Protegida rol="ADMINISTRADOR" menu={MENU_ADMIN}>{el}</Protegida>;
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/estudiante" element={E(<EstudianteInicio />)} />
        <Route path="/estudiante/evaluar" element={E(<Evaluacion />)} />
        <Route path="/estudiante/resultados" element={E(<MisResultados />)} />
        <Route path="/estudiante/recomendaciones" element={E(<Recomendaciones />)} />
        <Route path="/estudiante/perfil" element={E(<MiPerfil />)} />
        <Route path="/profesional" element={P(<Bandeja />)} />
        <Route path="/profesional/casos/:id" element={P(<Caso />)} />
        <Route path="/profesional/estudiantes" element={P(<Estudiantes />)} />
        <Route path="/profesional/seguimientos" element={P(<Seguimientos />)} />
        <Route path="/profesional/reportes" element={P(<Reportes />)} />
        <Route path="/admin" element={A(<AdminPanel />)} />
        <Route path="/admin/usuarios" element={A(<Usuarios />)} />
        <Route path="/admin/casos" element={A(<Casos />)} />
        <Route path="/admin/actividad" element={A(<Actividad />)} />
        <Route path="/admin/fuentes-externas" element={A(<FuentesExternas />)} />
        <Route path="/admin/modelo-nlp" element={A(<ModeloNLP />)} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </BrowserRouter>
  );
}