import { Link } from 'react-router'
import './EmptyState.css'

// A centered message with one way onward, used for the study page's empty
// states and for a deck that no longer exists
function EmptyState({ message, linkTo, linkLabel }) {
  return (
    <div className="empty-state">
      <p className="empty-state__message">{message}</p>
      <Link to={linkTo} className="button-primary">{linkLabel}</Link>
    </div>
  )
}

export default EmptyState
