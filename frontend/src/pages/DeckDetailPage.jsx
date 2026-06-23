import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router'
import {
  getDeck,
  updateDeck,
  deleteDeck,
  getCards,
  createCard,
  updateCard,
  deleteCard,
} from '../api'

function DeckDetailPage() {
  const { deckId } = useParams()
  const navigate = useNavigate()
  const [deck, setDeck] = useState(null)
  const [cards, setCards] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [deleteError, setDeleteError] = useState('')

  const [question, setQuestion] = useState('')
  const [answer, setAnswer] = useState('')
  const [createError, setCreateError] = useState('')

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
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }

    loadDeck()
  }, [deckId])

  async function handleCreateCard(e) {
    e.preventDefault()
    setCreateError('')

    try {
      const newCard = await createCard(deckId, question, answer)
      setCards([...cards, newCard])
      setQuestion('')
      setAnswer('')
    } catch (err) {
      setCreateError(err.message)
    }
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
      navigate('/dashboard')
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

  if (error) {
    return <p>{error}</p>
  }

  return (
    <div>
      {editingName ? (
        <form onSubmit={handleSaveName}>
          <input value={name} onChange={(e) => setName(e.target.value)} />
          <button type="submit">Save</button>
          <button type="button" onClick={() => setEditingName(false)}>
            Cancel
          </button>
          {editError && <p>{editError}</p>}
        </form>
      ) : (
        <>
          <h1>{deck.name}</h1>
          <button onClick={startEditingName}>Edit Deck Name</button>
          <button onClick={handleDeleteDeck}>Delete Deck</button>
        </>
      )}

      {deleteError && <p>{deleteError}</p>}

      {cards.length === 0 ? (
        <p>This deck has no cards yet. Add your first one!</p>
      ) : (
        <ul>
          {cards.map((card) =>
            editingCardId === card.card_id ? (
              <li key={card.card_id}>
                <form onSubmit={handleSaveCard}>
                  <input
                    value={editQuestion}
                    onChange={(e) => setEditQuestion(e.target.value)}
                  />
                  <input
                    value={editAnswer}
                    onChange={(e) => setEditAnswer(e.target.value)}
                  />
                  <button type="submit">Save</button>
                  <button type="button" onClick={() => setEditingCardId(null)}>
                    Cancel
                  </button>
                  {cardEditError && <p>{cardEditError}</p>}
                </form>
              </li>
            ) : (
              <li key={card.card_id}>
                {card.question}
                <button onClick={() => startEditingCard(card)}>Edit</button>
                <button onClick={() => handleDeleteCard(card)}>Delete</button>
              </li>
            )
          )}
        </ul>
      )}

      <h2>Add a Card</h2>
      <form onSubmit={handleCreateCard}>
        <label>
          Question
          <input value={question} onChange={(e) => setQuestion(e.target.value)} />
        </label>

        <label>
          Answer
          <input value={answer} onChange={(e) => setAnswer(e.target.value)} />
        </label>

        {createError && <p>{createError}</p>}

        <button type="submit">Add Card</button>
      </form>
    </div>
  )
}

export default DeckDetailPage
