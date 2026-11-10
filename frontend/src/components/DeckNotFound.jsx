import { Link } from 'react-router'
import './DeckNotFound.css'

// Shown when the API says the deck doesn't exist, e.g. it was deleted in
// another tab
function DeckNotFound() {
  return (
    <div className="deck-not-found">
      <p>This deck no longer exists.</p>
      <Link to="/dashboard">Back to dashboard</Link>
    </div>
  )
}

export default DeckNotFound
