import { describe, expect, it, vi } from 'vitest'
import { createCardsBulk, formatErrorDetail, generateCards, getDeck, getRemainingGenerations, loginUser } from './api'
import { jsonResponse, mockApi } from './test/helpers'

describe('formatErrorDetail', () => {
  it('returns a string detail as it is', () => {
    expect(formatErrorDetail('Deck not found')).toBe('Deck not found')
  })

  it('names the field for each validation error in a list', () => {
    const detail = [
      { loc: ['body', 'cards', 1, 'answer'], msg: 'String should have at least 1 character', input: '' },
      { loc: ['body', 'notes'], msg: 'String should have at most 2000 characters', input: 'long notes' },
    ]

    expect(formatErrorDetail(detail)).toBe(
      'answer: String should have at least 1 character; notes: String should have at most 2000 characters'
    )
  })

  it('leaves out a field name that is a list index or the whole body', () => {
    expect(formatErrorDetail([{ loc: ['body', 'cards', 0], msg: 'Field required' }])).toBe('Field required')
    expect(formatErrorDetail([{ loc: ['body'], msg: 'Invalid JSON' }])).toBe('Invalid JSON')
  })

  it('never shows the rejected input', () => {
    const detail = [{ loc: ['body', 'notes'], msg: 'Too long', input: 'my private notes' }]

    expect(formatErrorDetail(detail)).not.toContain('my private notes')
  })

  it('returns null when there is nothing usable', () => {
    expect(formatErrorDetail(undefined)).toBeNull()
    expect(formatErrorDetail([])).toBeNull()
    expect(formatErrorDetail({ unexpected: true })).toBeNull()
  })
})

describe('request errors', () => {
  it('shows a 422 list as a readable message with its status', async () => {
    mockApi({
      'GET /decks/1': jsonResponse(422, {
        detail: [{ loc: ['body', 'question'], msg: 'String should have at least 1 character' }],
      }),
    })

    const error = await getDeck(1).catch((err) => err)

    expect(error.message).toBe('question: String should have at least 1 character')
    expect(error.status).toBe(422)
  })

  it.each([429, 500, 502, 503])('shows the API message for a %i', async (status) => {
    mockApi({ 'GET /generations/remaining': jsonResponse(status, { detail: `Message for ${status}` }) })

    const error = await getRemainingGenerations().catch((err) => err)

    expect(error.message).toBe(`Message for ${status}`)
    expect(error.status).toBe(status)
  })

  it('falls back to the status when the error body is not JSON', async () => {
    mockApi({ 'GET /decks/1': jsonResponse(502, undefined) })

    await expect(getDeck(1)).rejects.toThrow('Request failed (502)')
  })

  it('explains a network failure', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('Failed to fetch')))

    await expect(getDeck(1)).rejects.toThrow("Couldn't reach the server. Check your connection and try again.")
  })

  it('clears the token and throws on a 401 while logged in', async () => {
    localStorage.setItem('token', 'expired-token')
    mockApi({ 'GET /decks/1': jsonResponse(401, { detail: 'Invalid token' }) })
    // jsdom can't navigate, so the redirect itself is only attempted
    vi.spyOn(console, 'error').mockImplementation(() => {})

    await expect(getDeck(1)).rejects.toThrow('Your session has expired. Please log in again.')
    expect(localStorage.getItem('token')).toBeNull()
  })

  it('shows the API message for a 401 when logged out, as at login', async () => {
    mockApi({ 'POST /auth/login': jsonResponse(401, { detail: 'Email or password incorrect' }) })

    await expect(loginUser('a@example.com', 'wrong')).rejects.toThrow('Email or password incorrect')
  })
})

describe('generation endpoints', () => {
  it('generateCards posts the notes to the deck', async () => {
    const calls = mockApi({
      'POST /decks/3/cards/generate': jsonResponse(200, { status: 'rejected', reason: 'No content', remaining: 4 }),
    })

    const result = await generateCards(3, 'Some notes')

    expect(calls).toEqual([{ method: 'POST', path: '/decks/3/cards/generate', body: { notes: 'Some notes' } }])
    expect(result.remaining).toBe(4)
  })

  it('createCardsBulk posts the cards in one request', async () => {
    const cards = [{ question: 'Q1', answer: 'A1' }, { question: 'Q2', answer: 'A2' }]
    const calls = mockApi({ 'POST /decks/3/cards/bulk': jsonResponse(201, []) })

    await createCardsBulk(3, cards)

    expect(calls).toEqual([{ method: 'POST', path: '/decks/3/cards/bulk', body: { cards } }])
  })

  it('getRemainingGenerations reads the remaining count', async () => {
    mockApi({ 'GET /generations/remaining': jsonResponse(200, { remaining: 3, limit: 5 }) })

    expect(await getRemainingGenerations()).toEqual({ remaining: 3, limit: 5 })
  })
})
