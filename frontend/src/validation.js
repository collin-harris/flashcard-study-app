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
