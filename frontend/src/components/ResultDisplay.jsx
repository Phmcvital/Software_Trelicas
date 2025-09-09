

import React from 'react';

const ResultDisplay = ({ result }) => {
  
  if (!result) {
    return null;
  }

  
  const { deslocamentos, reacoes, esforcos_por_barra } = result.resultados;

  
  const formatNumber = (num, decimals) => Number(num).toFixed(decimals);

  return (
    <div className="result-section">
      <h2>Resultados do Cálculo</h2>

      {}
      <div className="result-table-container">
        <h3>Deslocamentos Nodais</h3>
        <p>Valores em milímetros (mm)</p>
        <table>
          <thead>
            <tr>
              <th>Nó</th>
              <th>Deslocamento X (Ux)</th>
              <th>Deslocamento Y (Uy)</th>
            </tr>
          </thead>
          <tbody>
            {Object.entries(deslocamentos).map(([noId, u]) => (
              <tr key={noId}>
                <td>{noId}</td>
                {}
                <td>{formatNumber(u.Ux * 1000, 4)}</td>
                <td>{formatNumber(u.Uy * 1000, 4)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {}
      <div className="result-table-container">
        <h3>Reações nos Apoios</h3>
        <p>Valores em Newtons (N)</p>
        <table>
          <thead>
            <tr>
              <th>Nó</th>
              <th>Reação X (Rx)</th>
              <th>Reação Y (Ry)</th>
            </tr>
          </thead>
          <tbody>
            {Object.keys(reacoes).length > 0 ? (
              Object.entries(reacoes).map(([noId, r]) => (
                <tr key={noId}>
                  <td>{noId}</td>
                  <td>{formatNumber(r.Rx, 2)}</td>
                  <td>{formatNumber(r.Ry, 2)}</td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan="3">Não há reações de apoio (estrutura hipostática).</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {}
      <div className="result-table-container">
        <h3>Esforços Axiais nas Barras</h3>
        <p>Valores em Newtons (N)</p>
        <table>
          <thead>
            <tr>
              <th>Barra</th>
              <th>Nós</th>
              <th>Força Axial</th>
              <th>Tipo</th>
            </tr>
          </thead>
          <tbody>
            {Object.entries(esforcos_por_barra).map(([barraId, esforco]) => {
              const ehTracao = esforco.N_orientado >= 0;
              return (
                <tr key={barraId}>
                  <td>{barraId}</td>
                  <td>{`${esforco.no_i} → ${esforco.no_j}`}</td>
                  <td>{formatNumber(Math.abs(esforco.N_orientado), 2)}</td>
                  <td style={{ color: ehTracao ? 'blue' : 'red', fontWeight: 'bold' }}>
                    {ehTracao ? 'Tração' : 'Compressão'}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default ResultDisplay;