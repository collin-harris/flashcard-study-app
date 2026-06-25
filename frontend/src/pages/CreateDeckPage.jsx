import { useState } from 'react'
import { Link, useNavigate } from 'react-router'
import { createDeck } from '../api'
import './CreateDeckPage.css'

function CreateDeckPage() {
  const [name, setName] = useState('')
  const [error, setError] = useState('')
  const navigate = useNavigate()

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')

    try {
      await createDeck(name)
      navigate('/dashboard')
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <div className="form-page">
      <div className="form-card">
        <form onSubmit={handleSubmit}>
          <h1>Create Deck</h1>

          <label>
            Deck Name
            <input value={name} onChange={(e) => setName(e.target.value)} />
          </label>

          {error && <p className="error-message">{error}</p>}

          <div className="form-actions">
            <button type="submit" className="button-primary">Create</button>
            <Link to="/dashboard">Cancel</Link>
          </div>
        </form>
      </div>
    </div>
  )
}

export default CreateDeckPage
