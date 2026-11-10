import { act, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { jsonResponse, mockApi, renderApp } from '../test/helpers'

const DECK = { deck_id: 1, user_id: 1, name: 'Biology' }

const CARD = { card_id: 1, deck_id: 1, question: 'Q', answer: 'A' }

function mockDeckApi(routes = {}) {
  return mockApi({
    'GET /decks/1': jsonResponse(200, DECK),
    'GET /decks/1/cards': jsonResponse(200, [CARD]),
    'GET /generations/remaining': jsonResponse(200, { remaining: 5, limit: 5 }),
    ...routes,
  })
}

async function openAddCardForm(user) {
  await user.click(await screen.findByRole('button', { name: '+ Add a card' }))
}

function countCalls(calls, method) {
  return calls.filter((call) => call.method === method).length
}

describe('DeckDetailPage', () => {
  it('links to the generate page next to Add a card', async () => {
    mockDeckApi()
    const router = renderApp('/decks/1')
    const user = userEvent.setup()

    expect(await screen.findByRole('button', { name: '+ Add a card' })).toBeInTheDocument()
    await user.click(screen.getByRole('link', { name: 'Generate from notes' }))

    expect(await screen.findByRole('heading', { name: 'Generate Cards from Notes' })).toBeInTheDocument()
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

  it('says when the deck no longer exists, with a link to the dashboard', async () => {
    mockDeckApi({
      'GET /decks/1': jsonResponse(404, { detail: 'Deck not found' }),
      'GET /decks': jsonResponse(200, []),
    })
    const router = renderApp('/decks/1')
    const user = userEvent.setup()

    expect(await screen.findByText('This deck no longer exists.')).toBeInTheDocument()
    await user.click(screen.getByRole('link', { name: 'Back to dashboard' }))

    await waitFor(() => expect(router.state.location.pathname).toBe('/dashboard'))
  })

  it('shows other loading errors as they are', async () => {
    mockDeckApi({ 'GET /decks/1': jsonResponse(500, { detail: 'Server error' }) })
    renderApp('/decks/1')

    expect(await screen.findByText('Server error')).toBeInTheDocument()
    expect(screen.queryByText('This deck no longer exists.')).not.toBeInTheDocument()
  })

  it('replaces the deck page in history after deleting the deck', async () => {
    vi.spyOn(window, 'confirm').mockReturnValue(true)
    mockDeckApi({ 'DELETE /decks/1': jsonResponse(204, undefined), 'GET /decks': jsonResponse(200, []) })
    const router = renderApp(['/dashboard', '/decks/1'])
    const user = userEvent.setup()

    await user.click(await screen.findByRole('button', { name: 'Delete Deck' }))
    await waitFor(() => expect(router.state.location.pathname).toBe('/dashboard'))

    // Back skips the deleted deck's page
    await act(() => router.navigate(-1))

    expect(router.state.location.pathname).toBe('/dashboard')
  })
})

describe('adding a card', () => {
  it.each([
    ['   ', 'An answer', "Question can't be empty"],
    ['A question', '', "Answer can't be empty"],
    ['', ' \t', "Question can't be empty; Answer can't be empty"],
  ])('rejects question %j and answer %j without sending them', async (question, answer, message) => {
    const calls = mockDeckApi()
    renderApp('/decks/1')
    const user = userEvent.setup()
    await openAddCardForm(user)

    if (question) await user.type(screen.getByRole('textbox', { name: 'Question' }), question)
    if (answer) await user.type(screen.getByRole('textbox', { name: 'Answer' }), answer)
    await user.click(screen.getByRole('button', { name: 'Add Card' }))

    expect(screen.getByText(message)).toBeInTheDocument()
    expect(countCalls(calls, 'POST')).toBe(0)
  })

  it("shows the API's empty-field error in the same words", async () => {
    mockDeckApi({
      'POST /decks/1/cards': jsonResponse(422, {
        detail: [
          {
            type: 'string_too_short',
            loc: ['body', 'answer'],
            msg: 'String should have at least 1 character',
            ctx: { min_length: 1 },
          },
        ],
      }),
    })
    renderApp('/decks/1')
    const user = userEvent.setup()
    await openAddCardForm(user)

    await user.type(screen.getByRole('textbox', { name: 'Question' }), 'Q2')
    await user.type(screen.getByRole('textbox', { name: 'Answer' }), 'A2')
    await user.click(screen.getByRole('button', { name: 'Add Card' }))

    expect(await screen.findByText("Answer can't be empty")).toBeInTheDocument()
  })

  it('clears the form and moves focus back to the question after adding a card', async () => {
    mockDeckApi({ 'POST /decks/1/cards': jsonResponse(201, { card_id: 2, deck_id: 1, question: 'Q2', answer: 'A2' }) })
    renderApp('/decks/1')
    const user = userEvent.setup()
    await openAddCardForm(user)
    const questionBox = screen.getByRole('textbox', { name: 'Question' })

    await user.type(questionBox, 'Q2')
    await user.type(screen.getByRole('textbox', { name: 'Answer' }), 'A2')
    await user.click(screen.getByRole('button', { name: 'Add Card' }))

    expect(await screen.findByText('Q2')).toBeInTheDocument()
    expect(questionBox).toHaveValue('')
    expect(screen.getByRole('textbox', { name: 'Answer' })).toHaveValue('')
    expect(questionBox).toHaveFocus()
  })

  it('closes the form with Done', async () => {
    mockDeckApi()
    renderApp('/decks/1')
    const user = userEvent.setup()
    await openAddCardForm(user)

    expect(screen.queryByRole('button', { name: 'Cancel' })).not.toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Done' }))

    expect(screen.queryByRole('textbox', { name: 'Question' })).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: '+ Add a card' })).toBeInTheDocument()
  })
})

describe('editing a card', () => {
  it.each([
    ['question', "Question can't be empty"],
    ['answer', "Answer can't be empty"],
  ])('rejects a whitespace-only %s without sending it', async (field, message) => {
    const calls = mockDeckApi()
    renderApp('/decks/1')
    const user = userEvent.setup()
    await user.click(await screen.findByRole('button', { name: 'Edit' }))
    // The edit form's inputs have no labels: the question comes first
    const [questionBox, answerBox] = screen.getAllByRole('textbox')
    const box = field === 'question' ? questionBox : answerBox

    await user.clear(box)
    await user.type(box, '   ')
    await user.click(screen.getByRole('button', { name: 'Save' }))

    expect(screen.getByText(message)).toBeInTheDocument()
    expect(countCalls(calls, 'PATCH')).toBe(0)
  })
})
