import { useState, useEffect } from 'react'
import { api } from '../services/api'
import type { Transaction } from '../types'
import './Transactions.css'

export default function Transactions() {
  const [transactions, setTransactions] = useState<Transaction[]>([])
  const [loading, setLoading] = useState(true)
  const [showAddForm, setShowAddForm] = useState(false)
  const [formData, setFormData] = useState({
    type: 'expense',
    amount: '',
    category: '',
    description: '',
  })

  useEffect(() => {
    loadTransactions()
  }, [])

  const loadTransactions = async () => {
    try {
      setLoading(true)
      const data = await api.getTransactions(100)
      setTransactions(data.transactions)
    } catch (err) {
      console.error('Failed to load transactions:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await api.addTransaction({
        type: formData.type,
        amount: parseFloat(formData.amount),
        category: formData.category,
        description: formData.description,
      })
      setFormData({ type: 'expense', amount: '', category: '', description: '' })
      setShowAddForm(false)
      loadTransactions()
    } catch (err) {
      console.error('Failed to add transaction:', err)
    }
  }

  const handleDelete = async (id: string) => {
    if (!confirm('Delete this transaction?')) return
    try {
      await api.deleteTransaction(id)
      loadTransactions()
    } catch (err) {
      console.error('Failed to delete transaction:', err)
    }
  }

  if (loading) return <div className="loading">Loading transactions...</div>

  return (
    <div className="transactions">
      <div className="transactions-header">
        <h2>📊 Transactions</h2>
        <button onClick={() => setShowAddForm(!showAddForm)} className="add-btn">
          {showAddForm ? '✕ Cancel' : '+ Add Transaction'}
        </button>
      </div>

      {showAddForm && (
        <form onSubmit={handleSubmit} className="add-form">
          <div className="form-row">
            <select
              value={formData.type}
              onChange={(e) => setFormData({ ...formData, type: e.target.value })}
              required
            >
              <option value="expense">Expense</option>
              <option value="income">Income</option>
            </select>
            <input
              type="number"
              step="0.01"
              placeholder="Amount"
              value={formData.amount}
              onChange={(e) => setFormData({ ...formData, amount: e.target.value })}
              required
            />
          </div>
          <input
            type="text"
            placeholder="Category (e.g., groceries, salary)"
            value={formData.category}
            onChange={(e) => setFormData({ ...formData, category: e.target.value })}
            required
          />
          <input
            type="text"
            placeholder="Description"
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            required
          />
          <button type="submit" className="submit-btn">Add Transaction</button>
        </form>
      )}

      <div className="transactions-list">
        {transactions.length === 0 ? (
          <div className="empty-state">
            <p>No transactions yet. Add your first transaction!</p>
          </div>
        ) : (
          transactions.map((t) => (
            <div key={t.id} className={`transaction-item ${t.type}`}>
              <div className="transaction-info">
                <div className="transaction-header">
                  <span className="transaction-category">{t.category}</span>
                  <span className={`transaction-amount ${t.type}`}>
                    {t.type === 'income' ? '+' : '-'}${t.amount.toFixed(2)}
                  </span>
                </div>
                <div className="transaction-description">{t.description}</div>
                <div className="transaction-date">
                  {new Date(t.date).toLocaleDateString()}
                </div>
              </div>
              <button onClick={() => handleDelete(t.id)} className="delete-btn">
                🗑️
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  )
}
