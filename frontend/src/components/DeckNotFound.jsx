import EmptyState from './EmptyState'

// Shown when the API says the deck doesn't exist, e.g. it was deleted in
// another tab
function DeckNotFound() {
  return <EmptyState message="This deck no longer exists." linkTo="/dashboard" linkLabel="Back to Dashboard" />
}

export default DeckNotFound
