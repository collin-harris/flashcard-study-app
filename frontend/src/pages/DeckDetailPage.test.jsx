import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import { jsonResponse, mockApi, renderApp } from '../test/helpers'

const DECK = { deck_id: 1, user_id: 1, name: 'Biology' }

function mockDeckApi() {
  return mockApi({
    'GET /decks/1': jsonResponse(200, DECK),
    'GET /decks/1/cards': jsonResponse(200, [{ card_id: 1, deck_id: 1, question: 'Q', answer: 'A' }]),
    'GET /generations/remaining': jsonResponse(200, { remaining: 5, limit: 5 }),
  })
}

describe('DeckDetailPage', () => {
  it('links to the generate page next to Add a card', async () => {
    mockDeckApi()
    const router = renderApp('/decks/1')
    const user = userEvent.setup()

    expect(await screen.findByRole('button', { name: '+ Add a card' })).toBeInTheDocument()
    await user.click(screen.getByRole('link', { name: 'Generate from notes' }))

    expect(await screen.findByRole('heading', { name: 'Generate cards from notes' })).toBeInTheDocument()
    expect(router.state.location.pathname).toBe('/decks/1/generate')
  })

  it('shows how many cards were added, then clears it from history', async () => {
    mockDeckApi()
    const router = renderApp({ pathname: '/decks/1', state: { addedCount: 3 } })

    expect(await screen.findByText('Added 3 cards to this deck.')).toBeInTheDocument()
    // Cleared so a reload or Back doesn't show it again; the message stays for now
    await waitFor(() => expect(router.state.location.state).toBeNull())
    expect(screen.getByText('Added 3 cards to this deck.')).toBeInTheDocument()
  })

  it('says "card" for a single added card', async () => {
    mockDeckApi()
    renderApp({ pathname: '/decks/1', state: { addedCount: 1 } })

    expect(await screen.findByText('Added 1 card to this deck.')).toBeInTheDocument()
  })

  it('shows no message on a normal visit', async () => {
    mockDeckApi()
    renderApp('/decks/1')

    await screen.findByRole('heading', { name: 'Biology' })
    expect(screen.queryByText(/to this deck\./)).not.toBeInTheDocument()
  })
})
