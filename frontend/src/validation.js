export function isValidEmail(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)
}

export const NO_CARD_ERRORS = { question: '', answer: '' }

// One message per empty side, matching the ones formatErrorDetail makes
// from the API's own check
export function validateCard(question, answer) {
  return {
    question: question.trim() ? '' : "Question can't be empty.",
    answer: answer.trim() ? '' : "Answer can't be empty.",
  }
}

export function hasCardErrors(errors) {
  return Boolean(errors.question || errors.answer)
}

// The form's messages as one line of sentences
export function formMessage(...messages) {
  return messages.filter(Boolean).join(' ')
}

const PASSWORD_MIN_CHARACTERS = 8
// bcrypt, which hashes passwords on the server, uses only the first 72 bytes
const PASSWORD_MAX_BYTES = 72

// The same rules and messages as the API's registration check. Characters
// are counted as code points, as the API counts them.
export function validateRegistration({ name, email, password }) {
  const problems = []
  if (!name.trim()) {
    problems.push("Name can't be empty.")
  }
  if (!isValidEmail(email)) {
    problems.push('Enter a valid email address.')
  }
  if ([...password].length < PASSWORD_MIN_CHARACTERS) {
    problems.push(`Password must be at least ${PASSWORD_MIN_CHARACTERS} characters.`)
  } else if (new TextEncoder().encode(password).length > PASSWORD_MAX_BYTES) {
    problems.push('Password is too long. Use at most 72 characters, or fewer if it includes emoji or accented letters.')
  }
  return formMessage(...problems)
}

export function validateDeckName(name) {
  return name.trim() ? '' : "Deck name can't be empty."
}
