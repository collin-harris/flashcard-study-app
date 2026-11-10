export function isValidEmail(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)
}

// Matches the messages formatErrorDetail makes from the API's own check
export function validateCard(question, answer) {
  const problems = []
  if (!question.trim()) {
    problems.push("Question can't be empty")
  }
  if (!answer.trim()) {
    problems.push("Answer can't be empty")
  }
  return problems.join('; ')
}
