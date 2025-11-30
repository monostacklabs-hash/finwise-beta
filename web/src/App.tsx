import { useState } from 'react'
import Auth from './components/Auth'
import Chat from './components/Chat'
import Dashboard from './components/Dashboard'
import Transactions from './components/Transactions'
import Goals from './components/Goals'
import Debts from './components/Debts'
import { LandingPage } from './components/LandingPage'
import './App.css'

type View = 'dashboard' | 'chat' | 'transactions' | 'goals' | 'debts' | 'budgets' | 'recurring'

function App() {
  const [token, setToken] = useState<string | null>(localStorage.getItem('token'))
  const [currentView, setCurrentView] = useState<View>('dashboard')
  const [showLanding, setShowLanding] = useState<boolean>(!localStorage.getItem('hasVisited'))

  const handleLogin = (newToken: string) => {
    localStorage.setItem('token', newToken)
    setToken(newToken)
  }

  const handleLogout = () => {
    localStorage.removeItem('token')
    setToken(null)
  }

  const handleGetStarted = () => {
    localStorage.setItem('hasVisited', 'true')
    setShowLanding(false)
  }

  // Show landing page for first-time visitors
  if (showLanding && !token) {
    return <LandingPage onGetStarted={handleGetStarted} />
  }

  if (!token) {
    return (
      <div className="app">
        <Auth onLogin={handleLogin} />
      </div>
    )
  }

  return (
    <div className="app">
      <nav className="sidebar">
        <div className="sidebar-header">
          <h1>🤖 FinWise AI</h1>
          <p>AI Financial Assistant</p>
        </div>
        <div className="nav-links">
          <button
            className={currentView === 'dashboard' ? 'active' : ''}
            onClick={() => setCurrentView('dashboard')}
          >
            📊 Dashboard
          </button>
          <button
            className={currentView === 'chat' ? 'active' : ''}
            onClick={() => setCurrentView('chat')}
          >
            💬 AI Chat
          </button>
          <button
            className={currentView === 'transactions' ? 'active' : ''}
            onClick={() => setCurrentView('transactions')}
          >
            💰 Transactions
          </button>
          <button
            className={currentView === 'goals' ? 'active' : ''}
            onClick={() => setCurrentView('goals')}
          >
            🎯 Goals
          </button>
          <button
            className={currentView === 'debts' ? 'active' : ''}
            onClick={() => setCurrentView('debts')}
          >
            💳 Debts
          </button>
        </div>
        <button onClick={handleLogout} className="logout-btn">
          🚪 Logout
        </button>
      </nav>

      <main className="main-content">
        {currentView === 'dashboard' && <Dashboard onNavigate={setCurrentView} />}
        {currentView === 'chat' && <Chat token={token} onLogout={handleLogout} />}
        {currentView === 'transactions' && <Transactions />}
        {currentView === 'goals' && <Goals />}
        {currentView === 'debts' && <Debts />}
      </main>
    </div>
  )
}

export default App
