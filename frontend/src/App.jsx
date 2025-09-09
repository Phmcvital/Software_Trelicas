// frontend/src/App.jsx

import './App.css';
import UploaderTrelica from './components/uploaderTrelica';

function App() {
  return (
    <div className="App">
      <header className="App-header">
        <h1>Software para Análise de Treliças</h1>
        <p>Faça o upload de um arquivo .txt para calcular e visualizar os resultados</p>
      </header>
      <main>
        <UploaderTrelica />
      </main>
      <footer className="App-footer">
        <p>Grupo: Pedro Henrique Martins da Costa Vital, ...</p>
      </footer>
    </div>
  );
}

export default App;
