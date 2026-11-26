// Marca: el volcán Misti con el sol de Arequipa.
export default function Logo({ tono = "claro", tam = 36 }) {
  const montana = tono === "claro" ? "#FBF4E9" : "#0E3B43";
  return (
    <div className={`logo ${tono}`}>
      <svg width={tam} height={tam} viewBox="0 0 48 48" role="img" aria-label="Mente Sana AQP">
        <circle cx="24" cy="24" r="23" fill={tono === "claro" ? "#175562" : "#FBF4E9"} stroke="#C98B52" strokeWidth="1.5" />
        <circle cx="31" cy="16" r="6" fill="#C98B52" />
        <path d="M6 37 L21 13 L27 23 L32 17 L42 37 Z" fill={montana} />
        <path d="M17 19.5 L21 13 L25 19.5 L22 18 Z" fill="#B4532D" />
      </svg>
      <span className="logo-texto">Mente Sana <b>AQP</b></span>
    </div>
  );
}
