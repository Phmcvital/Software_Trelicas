import UploaderTrelica from './components/uploaderTrelica'
import './index.css'

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
        Grupo: RODRIGO DE OLIVEIRA PAZ, PEDRO HENRIQUE MARTINS DA COSTA VITAL, KAIKY RODRIGUES DE CASTRO, EDUARDO RODRIGUES MELO e FRANCISCO IVAN PONTES DO NASCIMENTO JUNIOR
      </footer>
    </div>
  );
}

export default App;
