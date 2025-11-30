import { useState, useEffect } from 'react'
import { api } from '../services/api'
import type { Debt } from '../types'
import './Debts.css'

export default function Debts() {
  const [debts, setDebts] = useState<Debt[]>([])
  const [loading, setLoading] = useState(true)
  const [showAddForm, setShowAddForm] = useState(false)

  useEffect(() => {
    loadDebts()
  }, [])

  const loadDebts = async () => {
    try {
      const data = await api.getDebts()
      setDebts(data.debts)
    } catch (err) {
      console.error('Failed to load debts:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    const formData = new FormData(e.target as HTMLFormElement)
    try {
      await api.addDebt({
        type: formData.get('type') as string,
        name: formData.get('name') as string,
        remaining_amount: parseFloat(formData.get('remaining_amount') as string),
        interest_rate: parseFloat(formData.get('interest_rate') as string),
        monthly_payment: parseFloat(formData.get('monthly_payment') as string),
      })
      setShowAddForm(false)
      loadDebts()
    } catch (err) {
      console.error('Failed to add debt:', err)
    }
  }

  const handlePayment = async (id: string) => {
    const amount = prompt('Enter payment amount:')
    if (!amount) return
    try {
      await api.makeDebtPayment(id, parseFloat(amount))
      loadDebts()
    } catch (err) {
      console.error('Failed to make payment:', err)
    }
  }

  if (loading) return <div className="loading">Loading debts...</div>

  return (
    <div className="debts">
      <div className="debts-header">
        <h2>💳 Debts & Loans</h2>
        <button onClick={() => setShowAddForm(!showAddForm)} className="add-btn">
          {showAddForm ? '✕ Cancel' : '+ Add Debt'}
        </button>
      </div>

      {showAddForm && (
        <form onSubmit={handleSubmit} className="add-form">
          <select name="type" required>
            <option value="">Select type</option>
            <option value="credit_card">Credit Card</option>
            <option value="student_loan">Student Loan</option>
            <option value="mortgage">Mortgage</option>
            <option value="personal_loan">Personal Loan</option>
            <option value="auto_loan">Auto Loan</option>
          </select>
          <input name="name" placeholder="Debt name" required />
          <input name="remaining_amount" type="number" step="0.01" placeholder="Remaining amount" required />
          <input name="interest_rate" type="number" step="0.01" placeholder="Interest rate (%)" required />
          <input name="monthly_payment" type="number" step="0.01" placeholder="Monthly payment" required />
          <button type="submit" className="submit-btn">Add Debt</button>
        </form>
      )}

      <div className="debts-list">
        {debts.length === 0 ? (
          <div className="empty-state">No debts tracked. Great job! 🎉</div>
        ) : (
          debts.map((debt) => (
            <div key={debt.id} className="debt-card">
              <div className="debt-header">
                <h3>{debt.name}</h3>
                <span className="debt-type">{debt.type.replace('_', ' ')}</span>
              </div>
              <div className="debt-amount">${debt.remaining_amount.toLocaleString()}</div>
              <div className="debt-details">
                <div>Interest: {debt.interest_rate}%</div>
                <div>Monthly: ${debt.monthly_payment.toLocaleString()}</div>
              </div>
              <button onClick={() => handlePayment(debt.id)} className="payment-btn">
                Make Payment
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  )
}
