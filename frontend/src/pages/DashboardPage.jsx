import { useState, useEffect } from 'react'
import { Link } from 'react-router'
import { getDecks } from '../api'
import './DashboardPage.css'

function DashboardPage() {
  const [decks, setDecks] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    async function loadDecks() {
      try {
        const data = await getDecks()
        setDecks(data)
      } catch (err) {
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }

    loadDecks()
  }, [])

  if (loading) {
    return <p>Loading...</p>
  }

  if (error) {
    return <p className="error-message">{error}</p>
  }

  return (
    <div>
      <div className="dashboard-page__header">
        <h1>Dashboard</h1>
        <Link to="/decks/new" className="button-primary">Create Deck</Link>
      </div>
      {decks.length === 0 ? (
        <p className="dashboard-page__empty">You have no decks yet. Create your first one!</p>
      ) : (
        <ul className="deck-list">
          {decks.map((deck) => (
            <li key={deck.deck_id} className="deck-list__item">
              <Link to={`/decks/${deck.deck_id}`}>{deck.name}</Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

export default DashboardPage
