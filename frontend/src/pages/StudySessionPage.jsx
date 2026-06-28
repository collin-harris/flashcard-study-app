import { useState, useEffect } from 'react'
import { Link, useParams } from 'react-router'
import { getCards, getDueCards, submitReview } from '../api'
import './StudySessionPage.css'

function StudySessionPage() {
  const { deckId, mode } = useParams()
  const [cards, setCards] = useState([])
  const [currentIndex, setCurrentIndex] = useState(0)
  const [isAnswerRevealed, setIsAnswerRevealed] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [reviewError, setReviewError] = useState('')

  useEffect(() => {
    async function loadCards() {
      try {
        const data = mode === 'review' ? await getDueCards(deckId) : await getCards(deckId)
        setCards(data)
      } catch (err) {
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }

    loadCards()
  }, [deckId, mode])

  const currentCard = cards[currentIndex]
  const isSessionComplete = currentIndex >= cards.length

  async function handleRate(rating) {
    setReviewError('')
    try {
      await submitReview(deckId, currentCard.card_id, rating)
      setCurrentIndex((prev) => prev + 1)
      setIsAnswerRevealed(false)
    } catch (err) {
      setReviewError(err.message)
    }
  }

  if (loading) {
    return <p>Loading...</p>
  }

  if (error) {
    return <p className="error-message">{error}</p>
  }

  if (cards.length === 0) {
    return (
      <div className="study-session">
        <div className="study-session__header">
          <Link to={`/decks/${deckId}`} className="study-session__exit">Back to Deck</Link>
        </div>
        <div className="study-session__content">
          <p className="study-session__message">
            {mode === 'review' ? 'No cards are due today!' : 'This deck has no cards to study.'}
          </p>
          <Link to={`/decks/${deckId}`} className="button-primary">Back to Deck</Link>
        </div>
      </div>
    )
  }

  if (isSessionComplete) {
    return (
      <div className="study-session">
        <div className="study-session__header">
          <Link to={`/decks/${deckId}`} className="study-session__exit">Back to Deck</Link>
        </div>
        <div className="study-session__content">
          <h1 className="session-summary__heading">Session Complete</h1>
          <p className="session-summary__count">
            You reviewed {cards.length} {cards.length === 1 ? 'card' : 'cards'}.
          </p>
          <Link to={`/decks/${deckId}`} className="button-primary">Back to Deck</Link>
        </div>
      </div>
    )
  }

  return (
    <div className="study-session">
      <div className="study-session__header">
        <Link to={`/decks/${deckId}`} className="study-session__exit">Back to Deck</Link>
        <span className="study-session__progress">Card {currentIndex + 1} of {cards.length}</span>
      </div>

      <div className="study-session__content">
        <div
          className="flip-card"
          onClick={() => setIsAnswerRevealed((prev) => !prev)}
        >
          <div key={currentIndex} className={`flip-card__inner ${isAnswerRevealed ? 'is-flipped' : ''}`}>
            <div className="flip-card__face flip-card__face--front">
              <p className="study-session__card-text">{currentCard.question}</p>
            </div>
            <div className="flip-card__face flip-card__face--back">
              <p className="study-session__card-text">{currentCard.answer}</p>
            </div>
          </div>
        </div>

        <button
          className="button-primary"
          onClick={() => setIsAnswerRevealed((prev) => !prev)}
        >
          {isAnswerRevealed ? 'Show Question' : 'Show Answer'}
        </button>

        {isAnswerRevealed && (
          <div className="rating-buttons-block">
            <div className="rating-buttons">
              {[0, 1, 2, 3, 4, 5].map((rating) => (
                <button
                  key={rating}
                  className={`rating-button rating-button--${rating}`}
                  onClick={() => handleRate(rating)}
                >
                  {rating}
                </button>
              ))}
            </div>
            <p className="rating-buttons__legend">
              Rate how well you recalled the answer — 0 means you completely forgot, 5 means it was easy.
            </p>
          </div>
        )}

        {reviewError && <p className="error-message">{reviewError}</p>}
      </div>
    </div>
  )
}

export default StudySessionPage
