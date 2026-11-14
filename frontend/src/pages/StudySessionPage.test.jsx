import { screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { jsonResponse, mockApi, renderApp } from '../test/helpers'

describe('StudySessionPage', () => {
  it('says when no cards are due, with a button back to the deck', async () => {
    mockApi({ 'GET /decks/1/study': jsonResponse(200, []) })
    renderApp('/decks/1/study/review')

    expect(await screen.findByText('No cards are due today.')).toBeInTheDocument()
    expect(screen.getAllByRole('link', { name: 'Back to Deck' })).toHaveLength(2)
  })

  it('says when the deck has no cards to study', async () => {
    mockApi({ 'GET /decks/1/cards': jsonResponse(200, []) })
    renderApp('/decks/1/study/free')

    expect(await screen.findByText('This deck has no cards to study.')).toBeInTheDocument()
  })
})
