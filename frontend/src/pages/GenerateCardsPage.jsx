import { useState, useEffect, useRef, useCallback } from 'react'
import { Link, useParams, useNavigate, useBlocker, useBeforeUnload } from 'react-router'
import { getDeck, getRemainingGenerations, generateCards, createCardsBulk } from '../api'
import DraftCard from '../components/DraftCard'
import './GenerateCardsPage.css'

const MAX_NOTES_LENGTH = 2000
const MAX_CARDS_PER_SAVE = 100
const LEAVE_MESSAGE = "Leave this page? Your generated cards haven't been saved and will be lost."

// Counted the way the API counts: after trimming, in characters (code
// points) rather than JavaScript's UTF-16 units
function countCharacters(text) {
  return [...text.trim()].length
}

function GenerateCardsPage() {
  const { deckId } = useParams()
  const navigate = useNavigate()
  const [deck, setDeck] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const [remaining, setRemaining] = useState(null)
  const [limit, setLimit] = useState(null)
  const [remainingError, setRemainingError] = useState('')
  // Incremented to reload the remaining count
  const [remainingReloads, setRemainingReloads] = useState(0)

  const [notes, setNotes] = useState('')
  const [isGenerating, setIsGenerating] = useState(false)
  const [generateError, setGenerateError] = useState('')
  const [rejectionReason, setRejectionReason] = useState('')

  const [drafts, setDrafts] = useState([])
  const [isSaving, setIsSaving] = useState(false)
  const [saveError, setSaveError] = useState('')

  // Refs, not state, guard against double submits: a second click can
  // arrive before the re-render that disables the button
  const generatingRef = useRef(false)
  const savingRef = useRef(false)
  const nextKeyRef = useRef(0)
  // Set just before leaving after a save, so the blocker lets it through
  const leavingRef = useRef(false)

  useEffect(() => {
    async function loadDeck() {
      try {
        const deckData = await getDeck(deckId)
        setDeck(deckData)
      } catch (err) {
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }

    loadDeck()
  }, [deckId])

  useEffect(() => {
    async function loadRemaining() {
      try {
        const data = await getRemainingGenerations()
        setRemaining(data.remaining)
        setLimit(data.limit)
        setRemainingError('')
      } catch {
        // Generating stays allowed: the server enforces the limits anyway
        setRemainingError("Couldn't load your remaining generations.")
      }
    }

    loadRemaining()
  }, [remainingReloads])

  // Unsaved work is any draft, or a generation still in flight, since that
  // request has already used up one of the user's generations
  const hasUnsavedWork = drafts.length > 0 || isGenerating

  const blocker = useBlocker(({ currentLocation, nextLocation }) =>
    hasUnsavedWork && !leavingRef.current && currentLocation.pathname !== nextLocation.pathname
  )

  useEffect(() => {
    if (blocker.state === 'blocked') {
      if (window.confirm(LEAVE_MESSAGE)) {
        blocker.proceed()
      } else {
        blocker.reset()
      }
    }
  }, [blocker])

  // Covers reloading and closing the tab. Browsers show their own message.
  useBeforeUnload(
    useCallback(
      (event) => {
        if (hasUnsavedWork && !leavingRef.current) {
          event.preventDefault()
          event.returnValue = ''
        }
      },
      [hasUnsavedWork]
    )
  )

  const notesLength = countCharacters(notes)
  const canGenerate = notesLength >= 1 && notesLength <= MAX_NOTES_LENGTH && remaining !== 0 && !isGenerating

  const hasEmptyField = drafts.some((draft) => !draft.question.trim() || !draft.answer.trim())
  const isOverCap = drafts.length > MAX_CARDS_PER_SAVE
  const canSave = drafts.length > 0 && !hasEmptyField && !isOverCap && !isSaving && !isGenerating

  async function handleGenerate(e) {
    e.preventDefault()
    if (!canGenerate || generatingRef.current) {
      return
    }
    generatingRef.current = true
    setIsGenerating(true)
    setGenerateError('')
    setRejectionReason('')

    try {
      const result = await generateCards(deckId, notes)
      setRemaining(result.remaining)
      if (result.status === 'rejected') {
        // The notes stay, so the user can edit them and try again
        setRejectionReason(result.reason)
      } else {
        const newDrafts = result.cards.map((card) => ({
          key: nextKeyRef.current++,
          question: card.question,
          answer: card.answer,
          source: card.source,
        }))
        setDrafts((current) => [...current, ...newDrafts])
        setNotes('')
      }
    } catch (err) {
      setGenerateError(err.message)
      // A failed request can still count toward the limits, and an error
      // response doesn't include the remaining count
      setRemainingReloads((count) => count + 1)
    } finally {
      generatingRef.current = false
      setIsGenerating(false)
    }
  }

  function updateDraft(key, field, value) {
    setDrafts((current) => current.map((draft) => (draft.key === key ? { ...draft, [field]: value } : draft)))
  }

  function removeDraft(key) {
    setDrafts((current) => current.filter((draft) => draft.key !== key))
  }

  async function handleSave() {
    if (!canSave || savingRef.current) {
      return
    }
    savingRef.current = true
    setIsSaving(true)
    setSaveError('')

    try {
      const cards = drafts.map(({ question, answer }) => ({ question, answer }))
      await createCardsBulk(deckId, cards)
      leavingRef.current = true
      navigate(`/decks/${deckId}`, { replace: true, state: { addedCount: cards.length } })
    } catch (err) {
      setSaveError(err.message)
      savingRef.current = false
      setIsSaving(false)
    }
  }

  if (loading) {
    return <p>Loading...</p>
  }

  if (error) {
    return <p className="error-message">{error}</p>
  }

  const cardWord = drafts.length === 1 ? 'card' : 'cards'

  return (
    <div className="generate-page">
      <div className="generate-page__header">
        <Link to={`/decks/${deckId}`} className="generate-page__back">Back to {deck.name}</Link>
        <h1>Generate Cards from Notes</h1>
      </div>

      <form onSubmit={handleGenerate} className="notes-form">
        <label>
          Paste your notes
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            rows={10}
            disabled={isGenerating}
          />
        </label>

        <div className="notes-form__meta">
          <span
            className={
              notesLength > MAX_NOTES_LENGTH ? 'notes-form__counter notes-form__counter--over' : 'notes-form__counter'
            }
          >
            {notesLength.toLocaleString('en-US')} / {MAX_NOTES_LENGTH.toLocaleString('en-US')} characters
          </span>
        </div>

        {remaining === 0 && (
          <p className="notes-form__hint">
            You have no generations left. Each one becomes available again 24 hours after it was used.
          </p>
        )}

        <div className="generate-page__actions">
          <button type="submit" className="button-primary" disabled={!canGenerate}>
            {isGenerating ? 'Generating...' : 'Generate'}
          </button>
          {remainingError ? (
            <span className="generate-page__remaining">{remainingError}</span>
          ) : (
            limit !== null && (
              <span className="generate-page__remaining">
                {remaining} of {limit} generations left
              </span>
            )
          )}
        </div>
      </form>

      <div aria-live="polite">
        {isGenerating && (
          <p className="generate-page__status">
            Generating cards. This usually takes 10 to 20 seconds.
          </p>
        )}
        {rejectionReason && (
          <p className="generate-page__rejection">
            <strong>No cards were generated.</strong> {rejectionReason}
          </p>
        )}
        {generateError && <p className="error-message">{generateError}</p>}
      </div>

      {drafts.length > 0 && (
        <section className="draft-review">
          <hr className="generate-page__divider" />
          <h2>Review {drafts.length} {cardWord}</h2>
          <p className="draft-review__hint">
            Edit or remove cards before saving. Nothing is added to the deck until you save.
          </p>

          <ul className="draft-list">
            {drafts.map((draft, index) => (
              <DraftCard
                key={draft.key}
                draft={draft}
                number={index + 1}
                onChange={updateDraft}
                onRemove={removeDraft}
                disabled={isSaving}
              />
            ))}
          </ul>

          {isOverCap && (
            <p className="error-message">
              You can save at most {MAX_CARDS_PER_SAVE} cards at once. Remove at least{' '}
              {drafts.length - MAX_CARDS_PER_SAVE} to continue.
            </p>
          )}
          {hasEmptyField && <p className="error-message">Every card needs a question and an answer.</p>}
          {saveError && <p className="error-message">{saveError}</p>}

          <div className="generate-page__actions">
            <button type="button" className="button-primary" onClick={handleSave} disabled={!canSave}>
              {isSaving ? 'Saving...' : `Save ${drafts.length} ${cardWord}`}
            </button>
          </div>
        </section>
      )}
    </div>
  )
}

export default GenerateCardsPage
