import { useState, useRef } from 'react'
import './PasswordInput.css'

function EyeIcon() {
  return (
    <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M1 12s4-7 11-7 11 7 11 7-4 7-11 7-11-7-11-7z" />
      <circle cx="12" cy="12" r="3" />
    </svg>
  )
}

function EyeOffIcon() {
  return (
    <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M1 12s4-7 11-7 11 7 11 7-4 7-11 7-11-7-11-7z" />
      <circle cx="12" cy="12" r="3" />
      <line x1="2" y1="22" x2="22" y2="2" />
    </svg>
  )
}

function PasswordInput({ value, onChange }) {
  const [isVisible, setIsVisible] = useState(false)
  const inputRef = useRef(null)

  function toggleVisibility() {
    // Browsers reset the selection to "select all" when an input's type
    // changes while it's focused. Capture the cursor position now, and
    // restore it once the type swap has actually been applied to the DOM,
    // so typing afterward continues from where the user left off instead
    // of overwriting the whole value.
    const cursorPosition = inputRef.current.selectionStart
    setIsVisible((prev) => !prev)
    requestAnimationFrame(() => {
      inputRef.current.focus()
      inputRef.current.setSelectionRange(cursorPosition, cursorPosition)
    })
  }

  return (
    <div className="password-field">
      <input
        ref={inputRef}
        type={isVisible ? 'text' : 'password'}
        value={value}
        onChange={onChange}
        className="password-field__input"
      />
      <button
        type="button"
        className="password-toggle"
        onClick={toggleVisibility}
        aria-label={isVisible ? 'Hide password' : 'Show password'}
      >
        {isVisible ? <EyeOffIcon /> : <EyeIcon />}
      </button>
    </div>
  )
}

export default PasswordInput
