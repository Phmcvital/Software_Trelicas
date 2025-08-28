import Header from './components/header.jsx'
import UploaderTrelica from './components/uploaderTrelica.jsx'

const App = () => {

  return (
    
    <div className="app">
      <Header className="app-header"/>

      <p>Faça o upload do arquivo de especificação da treliça</p>

      <main>
        <UploaderTrelica />
      </main>
    </div>
  )
}

export default App
