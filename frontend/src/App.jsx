import ChatBox from './components/ChatBox'
import './App.css'

function App() {
  return (
    <div className="app">
      <header className="app-header">
        <h1>ChatBot X Pro</h1>
        <p>Powered by DeepSeek R1</p>
      </header>
      <ChatBox />
    </div>
  )
}

export default App
