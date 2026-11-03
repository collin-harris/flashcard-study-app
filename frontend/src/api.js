const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
const TOKEN_KEY = 'token'

export function saveToken(token) {
  localStorage.setItem(TOKEN_KEY, token)
}

export function getToken() {
  return localStorage.getItem(TOKEN_KEY)
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY)
}

function apiError(message, status) {
  const error = new Error(message)
  error.status = status
  return error
}

// The API sends a string detail for the errors it raises itself, and a list
// of validation errors for a 422. Each item's loc ends with the field's name,
// e.g. ["body", "cards", 1, "answer"].
export function formatErrorDetail(detail) {
  if (typeof detail === 'string') {
    return detail
  }
  if (Array.isArray(detail) && detail.length > 0) {
    return detail
      .map((item) => {
        const field = item.loc?.[item.loc.length - 1]
        return typeof field === 'string' && field !== 'body' ? `${field}: ${item.msg}` : item.msg
      })
      .join('; ')
  }
  return null
}

async function request(path, options = {}) {
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  }

  const token = getToken()
  if (token) {
    headers.Authorization = `Bearer ${token}`
  }

  let response
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...options,
      headers,
    })
  } catch {
    throw apiError("Couldn't reach the server. Check your connection and try again.", null)
  }

  if (response.status === 401 && token) {
    clearToken()
    window.location.href = '/login'
    // Thrown rather than returned, so no caller carries on with an undefined
    // result while the redirect happens
    throw apiError('Your session has expired. Please log in again.', 401)
  }

  if (!response.ok) {
    let detail = null
    try {
      const errorBody = await response.json()
      detail = formatErrorDetail(errorBody.detail)
    } catch {
      // Not JSON, e.g. a proxy's error page
    }
    throw apiError(detail || `Request failed (${response.status})`, response.status)
  }

  if (response.status === 204) {
    return null
  }

  return response.json()
}

export function registerUser(name, email, password) {
  return request('/auth/register', {
    method: 'POST',
    body: JSON.stringify({ name, email, password }),
  })
}

export function loginUser(email, password) {
  return request('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  })
}

export function getDecks() {
  return request('/decks')
}

export function createDeck(name) {
  return request('/decks', {
    method: 'POST',
    body: JSON.stringify({ name }),
  })
}

export function getCards(deckId) {
  return request(`/decks/${deckId}/cards`)
}

export function createCard(deckId, question, answer) {
  return request(`/decks/${deckId}/cards`, {
    method: 'POST',
    body: JSON.stringify({ question, answer }),
  })
}

export function createCardsBulk(deckId, cards) {
  return request(`/decks/${deckId}/cards/bulk`, {
    method: 'POST',
    body: JSON.stringify({ cards }),
  })
}

export function generateCards(deckId, notes) {
  return request(`/decks/${deckId}/cards/generate`, {
    method: 'POST',
    body: JSON.stringify({ notes }),
  })
}

export function getRemainingGenerations() {
  return request('/generations/remaining')
}

export function getDeck(deckId) {
  return request(`/decks/${deckId}`)
}

export function updateDeck(deckId, name) {
  return request(`/decks/${deckId}`, {
    method: 'PATCH',
    body: JSON.stringify({ name }),
  })
}

export function updateCard(deckId, cardId, question, answer) {
  return request(`/decks/${deckId}/cards/${cardId}`, {
    method: 'PATCH',
    body: JSON.stringify({ question, answer }),
  })
}

export function deleteDeck(deckId) {
  return request(`/decks/${deckId}`, {
    method: 'DELETE',
  })
}

export function deleteCard(deckId, cardId) {
  return request(`/decks/${deckId}/cards/${cardId}`, {
    method: 'DELETE',
  })
}

export function getDueCards(deckId) {
  return request(`/decks/${deckId}/study`)
}

export function submitReview(deckId, cardId, rating) {
  return request(`/decks/${deckId}/cards/${cardId}/review`, {
    method: 'POST',
    body: JSON.stringify({ rating }),
  })
}
