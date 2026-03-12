import { useEffect, useRef, useState } from 'react'

const QUICK_ACTIONS = {
  Popular: [
    'Explain a concept',
    'Write some code',
    'Get advice on a topic',
    'Generate ideas',
    'Plan a project',
    'Answer a question',
  ],
  'Make images': [
    'Create an image',
    'Design a logo',
    'Generate art',
    'Edit an image',
    'Make a poster',
    'Create an icon',
  ],
  'Plan and prep': [
    'Plan a trip',
    'Create a schedule',
    'Organize a project',
    'Draft an outline',
    'Plan a budget',
    'Prepare for an event',
  ],
  'Get advice': [
    'Career advice',
    'Writing tips',
    'Learning strategies',
    'Tech recommendations',
    'Life advice',
    'Problem solving',
  ],
}

function ChatBox({ onFirstMessage, hasMessages }) {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [persona, setPersona] = useState('General Assistant')
  const [activeCategory, setActiveCategory] = useState('Popular')
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const updateAssistantMessage = (content) => {
    setMessages((currentMessages) => {
      const nextMessages = [...currentMessages]
      const lastIndex = nextMessages.length - 1

      if (lastIndex >= 0 && nextMessages[lastIndex].role === 'assistant') {
        nextMessages[lastIndex] = {
          ...nextMessages[lastIndex],
          content,
        }
      }

      return nextMessages
    })
  }

  const sendMessage = async (messageText) => {
    const trimmed = messageText.trim()
    if (!trimmed || loading) return

    if (messages.length === 0 && onFirstMessage) {
      onFirstMessage()
    }

    const userMessage = { role: 'user', content: trimmed }
    const assistantPlaceholder = { role: 'assistant', content: 'Streaming response...' }
    const newMessages = [...messages, userMessage, assistantPlaceholder]
    setMessages(newMessages)
    setInput('')
    setLoading(true)

    try {
      const history = messages.map(({ role, content }) => ({ role, content }))

      const res = await fetch('/api/chat/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: trimmed, history, useWeb: true, stream: true, persona }),
      })

      if (!res.ok) {
        const data = await res.json()
        updateAssistantMessage(`Error: ${data.error}`)
        return
      }

      const reader = res.body?.getReader()
      if (!reader) {
        updateAssistantMessage('Error: Streaming is not supported in this browser.')
        return
      }

      const decoder = new TextDecoder()
      let buffer = ''
      let assistantContent = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (!line.trim()) continue

          const payload = JSON.parse(line)

          if (payload.type === 'chunk') {
            assistantContent += payload.content
            updateAssistantMessage(assistantContent || 'Streaming response...')
          }

          if (payload.type === 'done') {
            updateAssistantMessage(assistantContent || 'Streaming response...')
          }
        }
      }
    } catch {
      updateAssistantMessage('Error: Could not connect to server.')
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    sendMessage(input)
  }

  return (
    <div className="chatbox">
      {messages.length === 0 ? (
        <div className="welcome-screen">
          <div className="welcome-greeting">Hi there. What should we dive into today?</div>

          <div className="task-categories">
            {Object.keys(QUICK_ACTIONS).map((category) => (
              <button
                key={category}
                className={`category-tab ${activeCategory === category ? 'active' : ''}`}
                onClick={() => setActiveCategory(category)}
              >
                {category}
              </button>
            ))}
          </div>

          <div className="quick-actions">
            {QUICK_ACTIONS[activeCategory].map((action) => (
              <button
                key={action}
                className="action-button"
                onClick={() => sendMessage(action)}
                disabled={loading}
              >
                {action}
              </button>
            ))}
          </div>
        </div>
      ) : (
        <div className="messages chat-mode">
          {messages.map((msg, i) => (
            <div key={i} className={`message ${msg.role}`}>
              <div className="message-content">{msg.content}</div>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>
      )}

      <form className="input-area" onSubmit={handleSubmit}>
        <select
          value={persona}
          onChange={(e) => setPersona(e.target.value)}
          disabled={loading}
          className="persona-select"
        >
          <option>General Assistant</option>
          <option>Support Agent</option>
          <option>Finance Advisor</option>
          <option>Recipe Recommender</option>
          <option>Travel Planner</option>
          <option>Nutritionist</option>
          <option>Social Media Influencer</option>
          <option>Programming Assistant</option>
          <option>Writing Coach</option>
          <option>Language Tutor</option>
          <option>Math Tutor</option>
          <option>History Storyteller</option>
          <option>CTO Coach</option>
          <option>Career Counselor</option>
          <option>Poet</option>
          <option>Standup Comedian</option>
          <option>Trivia Master</option>
          <option>Party Planner</option>
          <option>Movie Recommender</option>
          <option>Inspirational Quotes</option>
        </select>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Message ChatBot X..."
          disabled={loading}
          className="message-input"
        />
        <button type="submit" disabled={loading || !input.trim()} className="send-button">
          {loading ? '...' : 'Send'}
        </button>
      </form>
    </div>
  )
}

export default ChatBox
