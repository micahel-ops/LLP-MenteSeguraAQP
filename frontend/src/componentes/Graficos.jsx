// Gráficos simples hechos con HTML y CSS (sin librerías externas).
export function Barras({ items }) {
  const max = Math.max(1, ...items.map((i) => i.valor));
  return (
    <div>
      {items.map((i) => (
        <div className="barra-fila" key={i.etiqueta}>
          <span>{i.etiqueta}</span>
          <div className="barra-pista" role="img" aria-label={`${i.etiqueta}: ${i.valor}`}>
            <span style={{ width: `${(i.valor / max) * 100}%`, background: i.color || "var(--terracota)" }} />
          </div>
          <strong>{i.valor}</strong>
        </div>
      ))}
    </div>
  );
}

export function Columnas({ items }) {
  const max = Math.max(1, ...items.map((i) => i.valor));
  return (
    <div>
      <div className="columnas">
        {items.map((i) => (
          <div className="columna" key={i.etiqueta}>
            <span>{i.valor}</span>
            <span className="pilar" style={{ height: `${(i.valor / max) * 100}%` }} />
          </div>
        ))}
      </div>
      <div className="etiquetas-columnas">{items.map((i) => <span key={i.etiqueta}>{i.etiqueta}</span>)}</div>
    </div>
  );
}
