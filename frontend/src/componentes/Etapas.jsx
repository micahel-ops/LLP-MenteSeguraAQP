// Flujo del caso, inspirado en BPMN 2.0:
// evento de inicio -> tarea -> tarea -> compuerta -> evento de fin
export default function Etapas({ etapa, validacion }) {
  const decision = validacion ? (validacion.confirma_riesgo ? "Sí" : "No") : "?";
  const nodos = [
    { clave: 1, tipo: "evento", marca: "1", texto: "Evaluación registrada" },
    { clave: 2, tipo: "tarea", marca: "2", texto: "Análisis y revisión" },
    { clave: 3, tipo: "tarea", marca: "3", texto: "Seguimiento y derivación" },
    { clave: 4, tipo: "compuerta", marca: decision, texto: "¿Riesgo confirmado?" },
    { clave: 5, tipo: "fin", marca: "4", texto: "Cerrado y control" },
  ];
  // etapa 1..4 -> índice del nodo actual (0..4)
  const actual = { 1: 0, 2: 1, 3: 2, 4: 4 }[etapa] ?? 0;
  const estado = (i) => (i < actual || (etapa === 4 && i <= 3) ? "hecho" : i === actual ? "actual" : "");
  return (
    <div className="etapas" role="list" aria-label="Etapas del caso">
      {nodos.map((n, i) => (
        <div key={n.clave} style={{ display: "contents" }}>
          <div className={`nodo ${estado(i)}`} role="listitem" aria-current={estado(i) === "actual" ? "step" : undefined}>
            <div className={`forma ${n.tipo}`}><span>{n.marca}</span></div>
            <span>{n.texto}</span>
          </div>
          {i < nodos.length - 1 && <div className={`union ${estado(i) === "hecho" ? "hecha" : ""}`} aria-hidden="true" />}
        </div>
      ))}
    </div>
  );
}
