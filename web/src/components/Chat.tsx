import { useState, useRef, useEffect } from 'react'
import axios from 'axios'
import './Chat.css'

interface Message {
  role: 'user' | 'assistant'
  content: string
}

interface ChatProps {
  token: string
  onLogout?: () => void
}

export default function Chat({ token }: ChatProps) {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const sendMessage = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || loading) return

    const userMessage = input.trim()
    setInput('')
    setMessages(prev => [...prev, { role: 'user', content: userMessage }])
    setLoading(true)

    try {
      const response = await axios.post(
        '/api/v1/chat',
        { message: userMessage },
        { headers: { Authorization: `Bearer ${token}` } }
      )

      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: response.data.response 
      }])
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'Failed to send message'
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: `❌ Error: ${errorMsg}` 
      }])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="chat-container">
      <div className="chat-header">
        <h2>💬 AI Chat Assistant</h2>
      </div>

      <div className="messages">
        {messages.length === 0 && (
          <div className="welcome">
            <h2>Welcome! 👋</h2>
            <p>Ask me anything about your finances:</p>
            <ul>
              <li>"I spent $45 on groceries"</li>
              <li>"What's my financial health?"</li>
              <li>"Show me my recent expenses"</li>
              <li>"How can I save more money?"</li>
            </ul>
          </div>
        )}

        {messages.map((msg, idx) => (
          <div key={idx} className={`message ${msg.role}`}>
            <div className="message-content">
              {msg.content}
            </div>
          </div>
        ))}

        {loading && (
          <div className="message assistant">
            <div className="message-content typing">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <form onSubmit={sendMessage} className="input-form">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type your message..."
          disabled={loading}
        />
        <button type="submit" disabled={loading || !input.trim()}>
          Send
        </button>
      </form>
    </div>
  )
}
