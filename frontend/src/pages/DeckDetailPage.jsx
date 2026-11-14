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
import { NO_CARD_ERRORS, formMessage, hasCardErrors, validateCard, validateDeckName } from '../validation'
import DeckNotFound from '../components/DeckNotFound'
import './DeckDetailPage.css'

function addedCardsMessage(count) {
  return `${count} ${count === 1 ? 'card' : 'cards'} added.`
}

function DeckDetailPage() {
  const { deckId } = useParams()
  const navigate = useNavigate()
  const location = useLocation()
  // Shown under the action row until the user's next action here: cards
  // added with the form, or by the generate page, which sets addedCount.
  // Read once, so it stays after the history entry's state is cleared below.
  const [status, setStatus] = useState(() => {
    const addedCount = location.state?.addedCount
    return addedCount ? addedCardsMessage(addedCount) : ''
  })
  const [deck, setDeck] = useState(null)
  const [cards, setCards] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [notFound, setNotFound] = useState(false)
  const [deleteError, setDeleteError] = useState('')

  const [isAddingCard, setIsAddingCard] = useState(false)
  const [question, setQuestion] = useState('')
  const [answer, setAnswer] = useState('')
  const [createFieldErrors, setCreateFieldErrors] = useState(NO_CARD_ERRORS)
  const [createError, setCreateError] = useState('')
  const questionInputRef = useRef(null)
  const addButtonRef = useRef(null)
  // Set when the form closes, so focus goes back to the "+ Add a Card"
  // button that reappears, instead of being lost with the form
  const returnFocusRef = useRef(false)

  const [editingName, setEditingName] = useState(false)
  const [name, setName] = useState('')
  const [editError, setEditError] = useState('')

  const [editingCardId, setEditingCardId] = useState(null)
  const [editQuestion, setEditQuestion] = useState('')
  const [editAnswer, setEditAnswer] = useState('')
  const [editFieldErrors, setEditFieldErrors] = useState(NO_CARD_ERRORS)
  const [cardEditError, setCardEditError] = useState('')
  // Shown in the row of the card that couldn't be deleted, where the user
  // just clicked, rather than at the top of a possibly long list
  const [deleteCardError, setDeleteCardError] = useState(null)

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

  useEffect(() => {
    if (!isAddingCard && returnFocusRef.current) {
      returnFocusRef.current = false
      addButtonRef.current?.focus()
    }
  }, [isAddingCard])

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
    clearMessages()

    const fieldErrors = validateCard(question, answer)
    if (hasCardErrors(fieldErrors)) {
      setCreateFieldErrors(fieldErrors)
      return
    }

    try {
      const newCard = await createCard(deckId, question, answer)
      setCards([...cards, newCard])
      setQuestion('')
      setAnswer('')
      setStatus('Card added.')
      // Ready for the next card
      questionInputRef.current?.focus()
    } catch (err) {
      setCreateError(err.message)
    }
  }

  // The user's next action clears the last status and delete error
  function clearMessages() {
    setStatus('')
    setDeleteCardError(null)
  }

  function openAddCard() {
    setIsAddingCard(true)
    clearMessages()
  }

  function closeAddCard() {
    returnFocusRef.current = true
    setIsAddingCard(false)
    setQuestion('')
    setAnswer('')
    setCreateFieldErrors(NO_CARD_ERRORS)
    setCreateError('')
    clearMessages()
  }

  // Typing in a field clears its own message, and the last "Card added."
  function changeNewCard(field, value) {
    if (field === 'question') {
      setQuestion(value)
    } else {
      setAnswer(value)
    }
    setCreateFieldErrors((errors) => ({ ...errors, [field]: '' }))
    setStatus('')
  }

  function changeEditedCard(field, value) {
    if (field === 'question') {
      setEditQuestion(value)
    } else {
      setEditAnswer(value)
    }
    setEditFieldErrors((errors) => ({ ...errors, [field]: '' }))
  }

  function startEditingName() {
    clearMessages()
    setName(deck.name)
    setEditError('')
    setEditingName(true)
  }

  async function handleSaveName(e) {
    e.preventDefault()
    setEditError('')

    const problem = validateDeckName(name)
    if (problem) {
      setEditError(problem)
      return
    }

    try {
      const updatedDeck = await updateDeck(deckId, name)
      setDeck(updatedDeck)
      setEditingName(false)
    } catch (err) {
      setEditError(err.message)
    }
  }

  // Closing a form clears its messages: this one's show outside the form,
  // so they'd otherwise stay on screen after Cancel
  function cancelEditingName() {
    setEditingName(false)
    setEditError('')
  }

  function cancelEditingCard() {
    setEditingCardId(null)
    setEditFieldErrors(NO_CARD_ERRORS)
    setCardEditError('')
  }

  function startEditingCard(card) {
    setEditingCardId(card.card_id)
    setEditQuestion(card.question)
    setEditAnswer(card.answer)
    setEditFieldErrors(NO_CARD_ERRORS)
    setCardEditError('')
    clearMessages()
  }

  async function handleSaveCard(e) {
    e.preventDefault()
    setCardEditError('')

    const fieldErrors = validateCard(editQuestion, editAnswer)
    if (hasCardErrors(fieldErrors)) {
      setEditFieldErrors(fieldErrors)
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
    clearMessages()
    const confirmed = window.confirm(`Delete this card? This cannot be undone.`)
    if (!confirmed) {
      return
    }

    try {
      await deleteCard(deckId, card.card_id)
      setCards(cards.filter((c) => c.card_id !== card.card_id))
    } catch (err) {
      setDeleteCardError({ cardId: card.card_id, message: err.message })
    }
  }

  if (loading) {
    return <p>Loading...</p>
  }

  const createMessage = formMessage(createFieldErrors.question, createFieldErrors.answer, createError)
  const editMessage = formMessage(editFieldErrors.question, editFieldErrors.answer, cardEditError)

  if (notFound) {
    return <DeckNotFound />
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
            <button type="button" className="button-secondary" onClick={cancelEditingName}>
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

      {editError && <p className="error-message">{editError}</p>}
      {deleteError && <p className="error-message">{deleteError}</p>}

      <div className="study-actions">
        <Link to={`/decks/${deckId}/study/free`} className="study-actions__button">Free Study</Link>
        <Link to={`/decks/${deckId}/study/review`} className="study-actions__button">Spaced Repetition</Link>
      </div>

      <hr className="divider" />

      <div className="add-card-section">
        <div className="add-card-actions">
          <Link to={`/decks/${deckId}/generate`} className="button-primary">Generate from Notes</Link>
          {!isAddingCard && (
            <button ref={addButtonRef} className="button-outline" onClick={openAddCard}>
              + Add a Card
            </button>
          )}
        </div>

        {isAddingCard && (
          <form onSubmit={handleCreateCard} className="add-card-form">
            <label>
              Question
              <input
                ref={questionInputRef}
                value={question}
                onChange={(e) => changeNewCard('question', e.target.value)}
                autoFocus
              />
            </label>

            <label>
              Answer
              <input value={answer} onChange={(e) => changeNewCard('answer', e.target.value)} />
            </label>

            {createMessage && <p className="error-message">{createMessage}</p>}

            <div className="form-actions">
              <button type="submit" className="button-primary">Add Card</button>
              <button type="button" className="button-secondary" onClick={closeAddCard}>Done</button>
            </div>
          </form>
        )}

        <div aria-live="polite">
          {status && <p className="add-card-status">{status}</p>}
        </div>
      </div>

      <div className="card-list-section">
        <p className="card-count">{cards.length} {cards.length === 1 ? 'card' : 'cards'}</p>

        {cards.length === 0 ? (
          <p className="empty-message">
            This deck has no cards yet. Generate them from your notes, or add one by hand.
          </p>
        ) : (
          <ul className="card-list">
            {cards.map((card) =>
              editingCardId === card.card_id ? (
                <li key={card.card_id} className="card-list__item">
                  <form onSubmit={handleSaveCard} className="card-list__edit-form">
                    <input
                      value={editQuestion}
                      onChange={(e) => changeEditedCard('question', e.target.value)}
                    />
                    <input
                      value={editAnswer}
                      onChange={(e) => changeEditedCard('answer', e.target.value)}
                    />
                    <button type="submit" className="button-primary">Save</button>
                    <button type="button" className="button-secondary" onClick={cancelEditingCard}>
                      Cancel
                    </button>
                    {editMessage && <p className="error-message">{editMessage}</p>}
                  </form>
                </li>
              ) : (
                <li key={card.card_id} className="card-list__item">
                  <span className="card-list__question">{card.question}</span>
                  <div className="card-list__actions">
                    <button className="button-secondary" onClick={() => startEditingCard(card)}>Edit</button>
                    <button className="button-danger" onClick={() => handleDeleteCard(card)}>Delete</button>
                  </div>
                  {deleteCardError?.cardId === card.card_id && (
                    <p className="error-message card-list__error" role="alert">
                      {deleteCardError.message}
                    </p>
                  )}
                </li>
              )
            )}
          </ul>
        )}
      </div>
    </div>
  )
}

export default DeckDetailPage
