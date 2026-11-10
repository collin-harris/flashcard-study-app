import { useState, useEffect, useRef } from 'react'
import { Link, useLocation, useParams, useNavigate } from 'react-router'
import {
  getDeck,
  updateDeck,
  deleteDeck,
  getCards,
  createCard,
  updateCard,
  deleteCard,
} from '../api'
import { validateCard } from '../validation'
import './DeckDetailPage.css'

function DeckDetailPage() {
  const { deckId } = useParams()
  const navigate = useNavigate()
  const location = useLocation()
  // Set by the generate page after saving. Read once, so the message stays
  // after the history entry's state is cleared below.
  const [addedCount] = useState(location.state?.addedCount ?? null)
  const [deck, setDeck] = useState(null)
  const [cards, setCards] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [notFound, setNotFound] = useState(false)
  const [deleteError, setDeleteError] = useState('')

  const [isAddingCard, setIsAddingCard] = useState(false)
  const [question, setQuestion] = useState('')
  const [answer, setAnswer] = useState('')
  const [createError, setCreateError] = useState('')
  const questionInputRef = useRef(null)

  const [editingName, setEditingName] = useState(false)
  const [name, setName] = useState('')
  const [editError, setEditError] = useState('')

  const [editingCardId, setEditingCardId] = useState(null)
  const [editQuestion, setEditQuestion] = useState('')
  const [editAnswer, setEditAnswer] = useState('')
  const [cardEditError, setCardEditError] = useState('')

  useEffect(() => {
    async function loadDeck() {
      try {
        const deckData = await getDeck(deckId)
        const cardsData = await getCards(deckId)
        setDeck(deckData)
        setCards(cardsData)
      } catch (err) {
        if (err.status === 404) {
          setNotFound(true)
        } else {
          setError(err.message)
        }
      } finally {
        setLoading(false)
      }
    }

    loadDeck()
  }, [deckId])

  // Clear the added-cards state from this history entry, so reloading or
  // coming back to the page doesn't show the message again
  useEffect(() => {
    if (location.state?.addedCount) {
      navigate(location.pathname, { replace: true, state: null })
    }
  }, [location, navigate])

  async function handleCreateCard(e) {
    e.preventDefault()
    setCreateError('')

    const problem = validateCard(question, answer)
    if (problem) {
      setCreateError(problem)
      return
    }

    try {
      const newCard = await createCard(deckId, question, answer)
      setCards([...cards, newCard])
      setQuestion('')
      setAnswer('')
      // Ready for the next card
      questionInputRef.current?.focus()
    } catch (err) {
      setCreateError(err.message)
    }
  }

  function closeAddCard() {
    setIsAddingCard(false)
    setQuestion('')
    setAnswer('')
    setCreateError('')
  }

  function startEditingName() {
    setName(deck.name)
    setEditError('')
    setEditingName(true)
  }

  async function handleSaveName(e) {
    e.preventDefault()
    setEditError('')

    try {
      const updatedDeck = await updateDeck(deckId, name)
      setDeck(updatedDeck)
      setEditingName(false)
    } catch (err) {
      setEditError(err.message)
    }
  }

  function startEditingCard(card) {
    setEditingCardId(card.card_id)
    setEditQuestion(card.question)
    setEditAnswer(card.answer)
    setCardEditError('')
  }

  async function handleSaveCard(e) {
    e.preventDefault()
    setCardEditError('')

    const problem = validateCard(editQuestion, editAnswer)
    if (problem) {
      setCardEditError(problem)
      return
    }

    try {
      const updatedCard = await updateCard(deckId, editingCardId, editQuestion, editAnswer)
      setCards(cards.map((c) => (c.card_id === updatedCard.card_id ? updatedCard : c)))
      setEditingCardId(null)
    } catch (err) {
      setCardEditError(err.message)
    }
  }

  async function handleDeleteDeck() {
    const confirmed = window.confirm(`Delete deck "${deck.name}"? This cannot be undone.`)
    if (!confirmed) {
      return
    }

    try {
      await deleteDeck(deckId)
      navigate('/dashboard', { replace: true })
    } catch (err) {
      setDeleteError(err.message)
    }
  }

  async function handleDeleteCard(card) {
    const confirmed = window.confirm(`Delete this card? This cannot be undone.`)
    if (!confirmed) {
      return
    }

    try {
      await deleteCard(deckId, card.card_id)
      setCards(cards.filter((c) => c.card_id !== card.card_id))
    } catch (err) {
      setCardEditError(err.message)
    }
  }

  if (loading) {
    return <p>Loading...</p>
  }

  if (notFound) {
    return (
      <div className="not-found">
        <p className="empty-message">This deck no longer exists.</p>
        <Link to="/dashboard">Back to dashboard</Link>
      </div>
    )
  }

  if (error) {
    return <p className="error-message">{error}</p>
  }

  return (
    <div>
      <div className="deck-header">
        {editingName ? (
          <form onSubmit={handleSaveName} className="deck-header__edit-form">
            <input value={name} onChange={(e) => setName(e.target.value)} />
            <button type="submit" className="button-primary">Save</button>
            <button type="button" className="button-secondary" onClick={() => setEditingName(false)}>
              Cancel
            </button>
          </form>
        ) : (
          <>
            <h1>{deck.name}</h1>
            <div className="deck-header__actions">
              <button className="button-secondary" onClick={startEditingName}>Edit Deck Name</button>
              <button className="button-danger" onClick={handleDeleteDeck}>Delete Deck</button>
            </div>
          </>
        )}
      </div>

      {addedCount && (
        <p className="success-message">
          Added {addedCount} {addedCount === 1 ? 'card' : 'cards'} to this deck.
        </p>
      )}
      {editError && <p className="error-message">{editError}</p>}
      {deleteError && <p className="error-message">{deleteError}</p>}

      <div className="study-actions">
        <Link to={`/decks/${deckId}/study/free`} className="study-actions__button">Free Study</Link>
        <Link to={`/decks/${deckId}/study/review`} className="study-actions__button">Spaced Repetition</Link>
      </div>

      <hr className="divider" />

      <div className="card-list-section">
        <p className="card-count">{cards.length} {cards.length === 1 ? 'card' : 'cards'}</p>

        {cards.length === 0 ? (
          <p className="empty-message">This deck has no cards yet. Add your first one!</p>
        ) : (
          <ul className="card-list">
            {cards.map((card) =>
              editingCardId === card.card_id ? (
                <li key={card.card_id} className="card-list__item">
                  <form onSubmit={handleSaveCard} className="card-list__edit-form">
                    <input
                      value={editQuestion}
                      onChange={(e) => setEditQuestion(e.target.value)}
                    />
                    <input
                      value={editAnswer}
                      onChange={(e) => setEditAnswer(e.target.value)}
                    />
                    <button type="submit" className="button-primary">Save</button>
                    <button type="button" className="button-secondary" onClick={() => setEditingCardId(null)}>
                      Cancel
                    </button>
                    {cardEditError && <p className="error-message">{cardEditError}</p>}
                  </form>
                </li>
              ) : (
                <li key={card.card_id} className="card-list__item">
                  <span className="card-list__question">{card.question}</span>
                  <div className="card-list__actions">
                    <button className="button-secondary" onClick={() => startEditingCard(card)}>Edit</button>
                    <button className="button-danger" onClick={() => handleDeleteCard(card)}>Delete</button>
                  </div>
                </li>
              )
            )}
          </ul>
        )}
      </div>

      <hr className="divider" />

      <div className="add-card-section">
        {isAddingCard ? (
          <form onSubmit={handleCreateCard} className="add-card-form">
            <label>
              Question
              <input ref={questionInputRef} value={question} onChange={(e) => setQuestion(e.target.value)} />
            </label>

            <label>
              Answer
              <input value={answer} onChange={(e) => setAnswer(e.target.value)} />
            </label>

            {createError && <p className="error-message">{createError}</p>}

            <div className="form-actions">
              <button type="submit" className="button-primary">Add Card</button>
              <button type="button" className="button-secondary" onClick={closeAddCard}>Done</button>
            </div>
          </form>
        ) : (
          <div className="add-card-actions">
            <button className="add-card-trigger" onClick={() => setIsAddingCard(true)}>+ Add a card</button>
            <Link to={`/decks/${deckId}/generate`} className="add-card-trigger">Generate from notes</Link>
          </div>
        )}
      </div>
    </div>
  )
}

export default DeckDetailPage
