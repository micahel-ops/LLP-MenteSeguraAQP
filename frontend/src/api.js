import axios from "axios";

export const api = axios.create({ baseURL: import.meta.env.VITE_API_URL || "http://127.0.0.1:8000/api" });

// Agrega el token a cada petición si hay sesión iniciada
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Si el token venció (401) fuera del login, vuelve a la pantalla de ingreso
api.interceptors.response.use(
  (r) => r,
  (err) => {
    const esLogin = err.config?.url?.includes("/login");
    if (err.response?.status === 401 && !esLogin && localStorage.getItem("token")) {
      cerrarSesion();
      window.location.assign("/login");
    }
    return Promise.reject(err);
  }
);

export function guardarSesion(data) {
  localStorage.setItem("token", data.token);
  localStorage.setItem("usuario", JSON.stringify(data.usuario));
}

export function cerrarSesion() {
  localStorage.removeItem("token");
  localStorage.removeItem("usuario");
}

export function usuarioGuardado() {
  try {
    return JSON.parse(localStorage.getItem("usuario"));
  } catch {
    return null;
  }
}

export const rutaPorRol = {
  ESTUDIANTE: "/estudiante",
  PROFESIONAL: "/profesional",
  ADMINISTRADOR: "/admin",
};

export const ETIQUETA_ROL = { ESTUDIANTE: "Estudiante", PROFESIONAL: "Profesional", ADMINISTRADOR: "Administrador" };

// Mensaje de error legible a partir de la respuesta del servidor
export function mensajeError(err, porDefecto = "Ocurrió un error. Inténtalo de nuevo.") {
  const d = err?.response?.data?.detail;
  if (typeof d === "string") return d;
  if (!err?.response) return "No se pudo conectar con el servidor.";
  return porDefecto;
}

export function fecha(f, conHora = false) {
  if (!f) return "—";
  const d = new Date(String(f).replace(" ", "T"));
  if (isNaN(d)) return String(f);
  const opciones = conHora
    ? { day: "numeric", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit" }
    : { day: "numeric", month: "short", year: "numeric" };
  return d.toLocaleDateString("es-PE", opciones);
}

// Etiquetas
export const NIVEL_ESTUDIANTE = { BAJO: "Estable", MEDIO: "Atención sugerida", ALTO: "Apoyo prioritario" };
export const CLASE_NIVEL = { BAJO: "ok", MEDIO: "aviso", ALTO: "alto" };
export const NIVEL_PROFESIONAL = { BAJO: "Bajo", MEDIO: "Medio", ALTO: "Alto" };
export const SEGUIMIENTO_ESTUDIANTE = {
  NINGUNO: "—",
  PENDIENTE: "Pendiente de revisión",
  EN_SEGUIMIENTO: "En seguimiento",
  CERRADO: "Seguimiento cerrado",
};
export const ESTADO_ALERTA = { NUEVA: "Nueva", EN_REVISION: "En revisión", ATENDIDA: "Atendida", DESCARTADA: "Descartada" };
export const TIPO_SEGUIMIENTO = { CONTACTO: "Contacto", DERIVACION: "Derivación", CONTROL: "Control" };

// Recomendaciones por nivel de riesgo
export const RECOMENDACIONES = {
  BAJO: [
    "Mantén tus rutinas de sueño, alimentación y ejercicio.",
    "Continúa con tus actividades sociales y de ocio.",
    "Practica técnicas de relajación o mindfulness 5-10 min al día.",
    "Identifica y refuerza tus estrategias de afrontamiento actuales.",
    "Realiza autoevaluaciones periódicas para monitorear cambios.",
  ],
  MEDIO: [
    "Considera agendar una cita con el servicio de bienestar universitario.",
    "Comparte cómo te sientes con alguien de confianza (amigo, familiar, tutor).",
    "Establece una rutina diaria estructurada con horarios regulares.",
    "Limita consumo de alcohol, cafeína y sustancias.",
    "Practica técnicas de respiración y grounding cuando sientas ansiedad.",
    "Evita aislarte: mantén al menos una actividad social semanal.",
  ],
  ALTO: [
    "Busca apoyo profesional cuanto antes (psicólogo, psiquiatra, servicio de urgencias).",
    "Contacta la línea 113 (Minsa) - atención psicológica gratuita 24/7.",
    "Informa a tu red de apoyo cercana (familia, amigos, tutor) sobre tu situación.",
    "Evita tomar decisiones importantes mientras te sientas abrumado/a.",
    "Si tienes pensamientos de autolesión o suicidio, ve a urgencias o llama al 113 inmediatamente.",
    "Tu universidad tiene protocolos de apoyo y acompañamiento; acude a bienestar estudiantil.",
  ],
};
