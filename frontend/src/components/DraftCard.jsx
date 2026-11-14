import './DraftCard.css'

function DraftCard({ draft, number, onChange, onRemove, disabled }) {
  const isQuestionEmpty = !draft.question.trim()
  const isAnswerEmpty = !draft.answer.trim()

  return (
    <li className="draft-card">
      <div className="draft-card__header">
        <span className="draft-card__number">Card {number}</span>
        <button
          type="button"
          className="draft-card__remove"
          onClick={() => onRemove(draft.key)}
          disabled={disabled}
        >
          Remove
        </button>
      </div>

      <label>
        Question
        <textarea
          value={draft.question}
          onChange={(e) => onChange(draft.key, 'question', e.target.value)}
          rows={2}
          disabled={disabled}
          aria-invalid={isQuestionEmpty}
        />
      </label>

      <label>
        Answer
        <textarea
          value={draft.answer}
          onChange={(e) => onChange(draft.key, 'answer', e.target.value)}
          rows={2}
          disabled={disabled}
          aria-invalid={isAnswerEmpty}
        />
      </label>

      <div className="draft-card__source">
        <span className="draft-card__source-label">From your notes</span>
        <ul>
          {draft.source.map((excerpt, index) => (
            <li key={index}>{excerpt}</li>
          ))}
        </ul>
      </div>
    </li>
  )
}

export default DraftCard
