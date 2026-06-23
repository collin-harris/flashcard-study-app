const API_BASE_URL = 'http://localhost:8000'
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

async function request(path, options = {}) {
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  }

  const token = getToken()
  if (token) {
    headers.Authorization = `Bearer ${token}`
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
  })

  if (response.status === 401 && token) {
    clearToken()
    window.location.href = '/login'
    return
  }

  if (!response.ok) {
    const errorBody = await response.json()
    throw new Error(errorBody.detail || 'Request failed')
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
