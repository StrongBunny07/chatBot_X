import { useState, useRef, useEffect } from 'react'

function ChatBox() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const sendMessage = async (e) => {
    e.preventDefault()
    const trimmed = input.trim()
    if (!trimmed || loading) return

    const userMessage = { role: 'user', content: trimmed }
    const newMessages = [...messages, userMessage]
    setMessages(newMessages)
    setInput('')
    setLoading(true)

    try {
      const history = messages.map(({ role, content }) => ({ role, content }))

      const res = await fetch('/api/chat/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: trimmed, history }),
      })

      const data = await res.json()

      if (res.ok) {
        setMessages([...newMessages, { role: 'assistant', content: data.response }])
      } else {
        setMessages([...newMessages, { role: 'assistant', content: `Error: ${data.error}` }])
      }
    } catch {
      setMessages([...newMessages, { role: 'assistant', content: 'Error: Could not connect to server.' }])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="chatbox">
      <div className="messages">
        {messages.length === 0 && (
          <div className="welcome">
            <p>Hello! Ask me anything.</p>
          </div>
        )}
        {messages.map((msg, i) => (
          <div key={i} className={`message ${msg.role}`}>
            <div className="message-label">{msg.role === 'user' ? 'You' : 'AI'}</div>
            <div className="message-content">{msg.content}</div>
          </div>
        ))}
        {loading && (
          <div className="message assistant">
            <div className="message-label">AI</div>
            <div className="message-content thinking">Thinking...</div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
      <form className="input-area" onSubmit={sendMessage}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type your message..."
          disabled={loading}
        />
        <button type="submit" disabled={loading || !input.trim()}>
          Send Message
        </button>
      </form>
    </div>
  )
}

export default ChatBox
