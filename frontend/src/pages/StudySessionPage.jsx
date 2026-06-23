import { useState, useEffect } from 'react'
import { useParams } from 'react-router'
import { getCards, getDueCards, submitReview } from '../api'

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
    return <p>{error}</p>
  }

  if (cards.length === 0) {
    return <p>{mode === 'review' ? 'No cards are due today!' : 'This deck has no cards to study.'}</p>
  }

  if (isSessionComplete) {
    return <p>You reviewed {cards.length} cards. Session Complete.</p>
  }

  return (
    <div>
      <p>{currentCard.question}</p>
      {isAnswerRevealed ? (
        <>
          <p>{currentCard.answer}</p>
          {[0, 1, 2, 3, 4, 5].map((rating) => (
            <button key={rating} onClick={() => handleRate(rating)}>{rating}</button>
          ))}
          {reviewError && <p>{reviewError}</p>}
        </>
      ) : (
        <button onClick={() => setIsAnswerRevealed(true)}>Show Answer</button>
      )}
    </div>
  )
}

export default StudySessionPage
