// frontend/src/components/TrussVisualizer.jsx

import React, { useMemo } from 'react'

const TrussVisualizer = ({ initialData, results }) => {
  const visualData = useMemo(() => {
    if (!initialData || !initialData.nos || initialData.nos.length === 0) {
      return null;
    }

    const { nos, barras } = initialData;
    const esforcos = results?.resultados?.esforcos_por_barra || {};

    const PADDING = 40;
    const SVG_WIDTH = 800;
    const SVG_HEIGHT = 500;

    let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
    nos.forEach(no => {
      minX = Math.min(minX, no.x);
      maxX = Math.max(maxX, no.x);
      minY = Math.min(minY, no.y);
      maxY = Math.max(maxY, no.y);
    });

    const trussWidth = maxX - minX;
    const trussHeight = maxY - minY;

    // Garante que não dividimos por zero se a treliça for um ponto ou linha
    const effectiveTrussWidth = trussWidth > 0 ? trussWidth : 1;
    const effectiveTrussHeight = trussHeight > 0 ? trussHeight : 1;

    const scaleX = (SVG_WIDTH - 2 * PADDING) / effectiveTrussWidth;
    const scaleY = (SVG_HEIGHT - 2 * PADDING) / effectiveTrussHeight;
    const scale = Math.min(scaleX, scaleY);

    // Calcula os deslocamentos para centralizar e ajustar o eixo Y
    const scaledTrussWidth = trussWidth * scale;
    const scaledTrussHeight = trussHeight * scale;

    const offsetX = PADDING + (SVG_WIDTH - 2 * PADDING - scaledTrussWidth) / 2 - (minX * scale);
    const offsetY = PADDING + (SVG_HEIGHT - 2 * PADDING - scaledTrussHeight) / 2 + (minY * scale); // Ajuste principal aqui

    const nosMap = {};
    nos.forEach(no => {
      nosMap[no.id] = {
        id: no.id,
        x: no.x * scale + offsetX,
        // Inverte o eixo Y para que o Y positivo seja para cima no desenho SVG
        y: SVG_HEIGHT - (no.y * scale + offsetY),
        apoio: no.apoio
      };
    });

    const processedBarras = barras.map(barra => {
      const esforco = Object.values(esforcos).find(e => e.no_i === barra.no_i && e.no_j === barra.no_j);
      let color = '#888888';
      if (esforco) {
        color = esforco.N_orientado >= 0 ? 'blue' : 'red';
      }
      return {
        ...barra,
        color,
        no1: nosMap[barra.no_i],
        no2: nosMap[barra.no_j]
      };
    });

    return { nos: Object.values(nosMap), barras: processedBarras, SVG_WIDTH, SVG_HEIGHT };

  }, [initialData, results]);

  if (!visualData) {
    return <div>Carregue um arquivo para visualizar a treliça.</div>;
  }

  const { nos, barras, SVG_WIDTH, SVG_HEIGHT } = visualData;

  return (
    <div className="visualizer-container">
      <h3>Visualização da Estrutura</h3>
      <svg width={SVG_WIDTH} height={SVG_HEIGHT} className="truss-svg">
        {barras.map(barra => (
          <line
            key={barra.id}
            x1={barra.no1.x}
            y1={barra.no1.y}
            x2={barra.no2.x}
            y2={barra.no2.y}
            stroke={barra.color}
            strokeWidth="5"
          />
        ))}

        {nos.map(no => (
          <React.Fragment key={no.id}>
            <circle cx={no.x} cy={no.y} r="8" fill={no.apoio !== 'N' ? '#333' : '#ccc'} />
            <text x={no.x + 12} y={no.y + 5} fontSize="14" fill="#000">
              {no.id}
            </text>
          </React.Fragment>
        ))}
      </svg>
      <div className="legend">
        <div><span style={{ backgroundColor: 'blue' }}></span> Tração</div>
        <div><span style={{ backgroundColor: 'red' }}></span> Compressão</div>
        <div><span style={{ backgroundColor: '#888888' }}></span> Esforço Nulo/Não Calculado</div>
      </div>
    </div>
  );
};

export default TrussVisualizer