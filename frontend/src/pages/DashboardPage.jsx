import { useState, useEffect } from 'react'
import { Link } from 'react-router'
import { getDecks } from '../api'

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
    return <p>{error}</p>
  }

  return (
    <div>
      <h1>Dashboard</h1>
      <Link to="/decks/new">Create Deck</Link>
      {decks.length === 0 ? (
        <p>You have no decks yet. Create your first one!</p>
      ) : (
        <ul>
          {decks.map((deck) => (
            <li key={deck.deck_id}>
              <Link to={`/decks/${deck.deck_id}`}>{deck.name}</Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

export default DashboardPage
