
import { useState } from "react";
import ResultDisplay from './ResultDisplay';
import TrussVisualizer from './TrussVisualizer.jsx';

const UploaderTrelica = () => {
  const [jsonData, setJsonData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);

  const handleFileUpload = (event) => {
    const file = event.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      const content = e.target.result;
      try {
        const parsedData = parseTrelica(content);
        setJsonData(parsedData);
        setResult(null); 
        setError(null);
      } catch (error) {
        setError(error.message);
        setJsonData(null);
        setResult(null);
      }
    };
    reader.readAsText(file);
  };

  const parseTrelica = (content) => {
    const lines = content.split('\n').filter(line => line.trim() !== '');
    if (lines.length < 4) {
      throw new Error('Formato de arquivo inválido ou incompleto.');
    }

    const [numNos] = lines[0].split(';').map(val => parseInt(val.trim()));
    const nos = [];
    for (let i = 1; i <= numNos; i++) {
      const parts = lines[i].split(';').map(val => val.trim());
      const id = parts[0];
      const x = parseFloat(parts[1].replace(/\s/g, ''));
      const y = parseFloat(parts[2].replace(/\s/g, ''));
      nos.push({ id, x, y });
    }

    const matrizAdjacencia = [];
    let lineIndex = numNos + 1;
    for (let i = 0; i < numNos; i++) {
      const row = lines[lineIndex++].split(';').map(val => parseInt(val.trim()));
      matrizAdjacencia.push(row);
    }

    const cargas = [];
    for (let i = 0; i < numNos; i++) {
      const [px, py] = lines[lineIndex++].split(';').map(val =>
        parseFloat(val.trim().replace(/\s/g, ''))
      );
      cargas.push([px, py]);
    }

    const vinculos = [];
    for (let i = 0; i < numNos; i++) {
      vinculos.push(lines[lineIndex++].trim());
    }

    nos.forEach((no, index) => {
      no.carga = cargas[index];
      no.apoio = vinculos[index];
    });

    const barras = [];
    let barraId = 1;
    for (let i = 0; i < numNos; i++) {
      for (let j = i + 1; j < numNos; j++) {
        if (matrizAdjacencia[i][j] === 1) {
          barras.push({
            id: barraId++,
            no_i: nos[i].id,
            no_j: nos[j].id,
            E: 210000000000,
            A: 0.01
          });
        }
      }
    }
    return { nos, barras };
  };

  const sendToBackend = async () => {
    if (!jsonData) return;
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await fetch('http:
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(jsonData)
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `Erro no servidor: ${response.status}`);
      }

      const resultData = await response.json();
      setResult({ resultados: resultData });
    } catch (error) {
      setError(`Erro ao enviar dados: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="trelica-uploader">
      <div className="upload-section">
        <h2>Upload do Arquivo</h2>
        <input
          type="file"
          accept=".txt"
          onChange={handleFileUpload}
          disabled={loading}
        />
      </div>

      {loading && <div className="loading">Processando...</div>}

      {error && (
        <div className="error">
          <h3>Erro</h3>
          <p>{error}</p>
        </div>
      )}

      {jsonData && (
        <div className="preview-section">
          <h2>Pré-visualização dos Dados</h2>
          <div className="data-preview">
            <h3>Nós ({jsonData.nos.length})</h3>
            <ul>
              {jsonData.nos.map(no => (
                <li key={no.id}>
                  {no.id}: ({no.x}, {no.y}), Carga: [{no.carga.join(', ')}], Apoio: {no.apoio}
                </li>
              ))}
            </ul>

            <h3>Barras ({jsonData.barras.length})</h3>
            <ul>
              {jsonData.barras.map(barra => (
                <li key={barra.id}>
                  Barra {barra.id}: {barra.no_i} → {barra.no_j}
                </li>
              ))}
            </ul>
          </div>

          <button onClick={sendToBackend} disabled={loading}>
            Enviar para Cálculo
          </button>
        </div>
      )}

      {result && (
        <>
          <TrussVisualizer initialData={jsonData} results={result} />
          <ResultDisplay result={result} />
        </>
      )}
    </div>
  );
};

export default UploaderTrelica;