import { act, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import { jsonResponse, mockApi, renderApp } from '../test/helpers'

describe('CreateDeckPage', () => {
  it("opens the new deck's page, replacing the create form in history", async () => {
    const calls = mockApi({
      'POST /decks': jsonResponse(201, { deck_id: 2, user_id: 1, name: 'Chemistry' }),
      'GET /decks/2': jsonResponse(200, { deck_id: 2, user_id: 1, name: 'Chemistry' }),
      'GET /decks/2/cards': jsonResponse(200, []),
      'GET /decks': jsonResponse(200, []),
    })
    const router = renderApp(['/dashboard', '/decks/new'])
    const user = userEvent.setup()

    await user.type(screen.getByRole('textbox', { name: 'Deck Name' }), 'Chemistry')
    await user.click(screen.getByRole('button', { name: 'Create' }))

    expect(await screen.findByRole('heading', { name: 'Chemistry' })).toBeInTheDocument()
    expect(router.state.location.pathname).toBe('/decks/2')
    expect(calls.find((call) => call.method === 'POST').body).toEqual({ name: 'Chemistry' })

    // Back goes to the dashboard, skipping the finished create form
    await act(() => router.navigate(-1))

    expect(router.state.location.pathname).toBe('/dashboard')
  })

  it.each(['', '   '])('says the deck name can\'t be empty (%j) before sending anything', async (name) => {
    const calls = mockApi({})
    renderApp(['/dashboard', '/decks/new'])
    const user = userEvent.setup()

    if (name) await user.type(screen.getByRole('textbox', { name: 'Deck Name' }), name)
    await user.click(screen.getByRole('button', { name: 'Create' }))

    expect(screen.getByText("Deck name can't be empty.")).toBeInTheDocument()
    expect(calls).toHaveLength(0)
  })

  it("shows the API's deck name message", async () => {
    mockApi({
      'POST /decks': jsonResponse(422, {
        detail: [{ type: 'empty_text', loc: ['body', 'name'], msg: "Deck name can't be empty." }],
      }),
    })
    renderApp(['/dashboard', '/decks/new'])
    const user = userEvent.setup()

    await user.type(screen.getByRole('textbox', { name: 'Deck Name' }), 'Chemistry')
    await user.click(screen.getByRole('button', { name: 'Create' }))

    expect(await screen.findByText("Deck name can't be empty.")).toBeInTheDocument()
  })

  it('leaves its message behind when cancelled, and starts clean next time', async () => {
    mockApi({ 'GET /decks': jsonResponse(200, []) })
    const router = renderApp(['/dashboard', '/decks/new'])
    const user = userEvent.setup()
    await user.click(screen.getByRole('button', { name: 'Create' }))
    expect(screen.getByText("Deck name can't be empty.")).toBeInTheDocument()

    await user.click(screen.getByRole('link', { name: 'Cancel' }))
    await screen.findByRole('heading', { name: 'Dashboard' })
    expect(screen.queryByText("Deck name can't be empty.")).not.toBeInTheDocument()

    await act(() => router.navigate('/decks/new'))
    expect(await screen.findByRole('heading', { name: 'Create Deck' })).toBeInTheDocument()
    expect(screen.queryByText("Deck name can't be empty.")).not.toBeInTheDocument()
  })
})

