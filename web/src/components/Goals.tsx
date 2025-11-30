import { useState, useEffect } from 'react'
import { api } from '../services/api'
import type { Goal } from '../types'
import './Goals.css'

export default function Goals() {
  const [goals, setGoals] = useState<Goal[]>([])
  const [loading, setLoading] = useState(true)
  const [showAddForm, setShowAddForm] = useState(false)
  const [formData, setFormData] = useState({
    name: '',
    target_amount: '',
    target_date: '',
    current_amount: '0',
  })

  useEffect(() => {
    loadGoals()
  }, [])

  const loadGoals = async () => {
    try {
      setLoading(true)
      const data = await api.getGoals()
      setGoals(data.goals)
    } catch (err) {
      console.error('Failed to load goals:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await api.addGoal({
        name: formData.name,
        target_amount: parseFloat(formData.target_amount),
        target_date: formData.target_date,
        current_amount: parseFloat(formData.current_amount),
      })
      setFormData({ name: '', target_amount: '', target_date: '', current_amount: '0' })
      setShowAddForm(false)
      loadGoals()
    } catch (err) {
      console.error('Failed to add goal:', err)
    }
  }

  const handleAddProgress = async (id: string) => {
    const amount = prompt('Enter amount to add:')
    if (!amount) return
    try {
      await api.updateGoalProgress(id, parseFloat(amount))
      loadGoals()
    } catch (err) {
      console.error('Failed to update goal:', err)
    }
  }

  const handleDelete = async (id: string) => {
    if (!confirm('Delete this goal?')) return
    try {
      await api.deleteGoal(id)
      loadGoals()
    } catch (err) {
      console.error('Failed to delete goal:', err)
    }
  }

  if (loading) return <div className="loading">Loading goals...</div>

  return (
    <div className="goals">
      <div className="goals-header">
        <h2>🎯 Financial Goals</h2>
        <button onClick={() => setShowAddForm(!showAddForm)} className="add-btn">
          {showAddForm ? '✕ Cancel' : '+ Add Goal'}
        </button>
      </div>

      {showAddForm && (
        <form onSubmit={handleSubmit} className="add-form">
          <input
            type="text"
            placeholder="Goal name (e.g., Emergency Fund)"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            required
          />
          <div className="form-row">
            <input
              type="number"
              step="0.01"
              placeholder="Target amount"
              value={formData.target_amount}
              onChange={(e) => setFormData({ ...formData, target_amount: e.target.value })}
              required
            />
            <input
              type="number"
              step="0.01"
              placeholder="Current amount"
              value={formData.current_amount}
              onChange={(e) => setFormData({ ...formData, current_amount: e.target.value })}
            />
          </div>
          <input
            type="date"
            value={formData.target_date}
            onChange={(e) => setFormData({ ...formData, target_date: e.target.value })}
            required
          />
          <button type="submit" className="submit-btn">Add Goal</button>
        </form>
      )}

      <div className="goals-list">
        {goals.length === 0 ? (
          <div className="empty-state">
            <p>No goals yet. Set your first financial goal!</p>
          </div>
        ) : (
          goals.map((goal) => (
            <div key={goal.id} className="goal-card">
              <div className="goal-header">
                <h3>{goal.name}</h3>
                <span className="goal-status">{goal.status}</span>
              </div>
              <div className="goal-progress">
                <div className="progress-bar">
                  <div
                    className="progress-fill"
                    style={{ width: `${Math.min(goal.progress_percentage, 100)}%` }}
                  />
                </div>
                <span className="progress-text">
                  {goal.progress_percentage.toFixed(1)}%
                </span>
              </div>
              <div className="goal-amounts">
                <span>${goal.current_amount.toLocaleString()}</span>
                <span className="target">of ${goal.target_amount.toLocaleString()}</span>
              </div>
              <div className="goal-date">
                Target: {new Date(goal.target_date).toLocaleDateString()}
              </div>
              <div className="goal-actions">
                <button onClick={() => handleAddProgress(goal.id)} className="progress-btn">
                  + Add Progress
                </button>
                <button onClick={() => handleDelete(goal.id)} className="delete-btn">
                  Delete
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}
