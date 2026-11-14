import { useState } from 'react'
import { Link, useNavigate } from 'react-router'
import { createDeck } from '../api'
import { validateDeckName } from '../validation'
import './CreateDeckPage.css'

function CreateDeckPage() {
  const [name, setName] = useState('')
  const [error, setError] = useState('')
  const navigate = useNavigate()

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')

    const problem = validateDeckName(name)
    if (problem) {
      setError(problem)
      return
    }

    try {
      const deck = await createDeck(name)
      navigate(`/decks/${deck.deck_id}`, { replace: true })
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
