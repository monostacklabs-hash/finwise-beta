import { useState, useEffect } from 'react'
import { api } from '../services/api'
import type { FinancialHealth } from '../types'
import './Dashboard.css'

interface DashboardProps {
  onNavigate: (view: 'dashboard' | 'chat' | 'transactions' | 'goals' | 'debts' | 'budgets' | 'recurring') => void
}

export default function Dashboard({ onNavigate }: DashboardProps) {
  const [health, setHealth] = useState<FinancialHealth | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    loadHealth()
  }, [])

  const loadHealth = async () => {
    try {
      setLoading(true)
      const data = await api.getFinancialHealth()
      setHealth(data)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load financial health')
    } finally {
      setLoading(false)
    }
  }

  if (loading) return <div className="loading">Loading dashboard...</div>
  if (error) return <div className="error">{error}</div>
  if (!health) return null

  const getScoreColor = (score: number) => {
    if (score >= 80) return '#10b981'
    if (score >= 60) return '#f59e0b'
    return '#ef4444'
  }

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h2>Financial Dashboard</h2>
        <button onClick={loadHealth} className="refresh-btn">🔄 Refresh</button>
      </div>

      <div className="health-score-card">
        <div className="score-circle" style={{ borderColor: getScoreColor(health.health_score) }}>
          <span className="score">{health.health_score}</span>
          <span className="score-label">Health Score</span>
        </div>
        <p className="assessment">{health.assessment}</p>
      </div>

      <div className="metrics-grid">
        <div className="metric-card">
          <span className="metric-label">Net Worth</span>
          <span className="metric-value">${health.net_worth.toLocaleString()}</span>
        </div>
        <div className="metric-card">
          <span className="metric-label">Total Income</span>
          <span className="metric-value income">${health.total_income.toLocaleString()}</span>
        </div>
        <div className="metric-card">
          <span className="metric-label">Total Expenses</span>
          <span className="metric-value expense">${health.total_expenses.toLocaleString()}</span>
        </div>
        <div className="metric-card">
          <span className="metric-label">Total Debt</span>
          <span className="metric-value debt">${health.total_debt.toLocaleString()}</span>
        </div>
        <div className="metric-card">
          <span className="metric-label">Savings Rate</span>
          <span className="metric-value">{(health.savings_rate * 100).toFixed(1)}%</span>
        </div>
        <div className="metric-card">
          <span className="metric-label">Debt-to-Income</span>
          <span className="metric-value">{(health.debt_to_income_ratio * 100).toFixed(1)}%</span>
        </div>
      </div>

      <div className="recommendations-card">
        <h3>💡 AI Recommendations</h3>
        <ul>
          {health.recommendations.map((rec, idx) => (
            <li key={idx}>{rec}</li>
          ))}
        </ul>
      </div>

      <div className="quick-actions">
        <button onClick={() => onNavigate('transactions')} className="action-btn">
          📊 Transactions
        </button>
        <button onClick={() => onNavigate('goals')} className="action-btn">
          🎯 Goals
        </button>
        <button onClick={() => onNavigate('debts')} className="action-btn">
          💳 Debts
        </button>
        <button onClick={() => onNavigate('budgets')} className="action-btn">
          💰 Budgets
        </button>
      </div>
    </div>
  )
}
