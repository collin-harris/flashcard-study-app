import { act, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import { jsonResponse, mockApi, renderApp } from '../test/helpers'

describe('CreateDeckPage', () => {
  it('replaces itself in history after creating the deck', async () => {
    const calls = mockApi({
      'POST /decks': jsonResponse(201, { deck_id: 2, user_id: 1, name: 'Chemistry' }),
      'GET /decks': jsonResponse(200, []),
    })
    const router = renderApp(['/dashboard', '/decks/new'])
    const user = userEvent.setup()

    await user.type(screen.getByRole('textbox', { name: 'Deck Name' }), 'Chemistry')
    await user.click(screen.getByRole('button', { name: 'Create' }))
    await waitFor(() => expect(router.state.location.pathname).toBe('/dashboard'))
    expect(calls.find((call) => call.method === 'POST').body).toEqual({ name: 'Chemistry' })

    // Back skips the finished create form
    await act(() => router.navigate(-1))

    expect(router.state.location.pathname).toBe('/dashboard')
  })
})
