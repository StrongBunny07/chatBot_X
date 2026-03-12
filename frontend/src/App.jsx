import { useState } from 'react'
import ChatBox from './components/ChatBox'
import './App.css'

function App() {
  const [hasMessages, setHasMessages] = useState(false)

  return (
    <div className="app">
      <header className="app-header">
        <h1>ChatBot X Pro</h1>
        <p>Powered by Qwen 2.5</p>
      </header>
      <ChatBox onFirstMessage={() => setHasMessages(true)} hasMessages={hasMessages} />
    </div>
  )
}

export default App
