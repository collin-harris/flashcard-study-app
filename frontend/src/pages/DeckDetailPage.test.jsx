import { act, screen, waitFor, within } from '@testing-library/react'
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
  await user.click(await screen.findByRole('button', { name: '+ Add a Card' }))
}

function countCalls(calls, method) {
  return calls.filter((call) => call.method === method).length
}

describe('DeckDetailPage', () => {
  it('links to the generate page next to Add a card', async () => {
    mockDeckApi()
    const router = renderApp('/decks/1')
    const user = userEvent.setup()

    expect(await screen.findByRole('button', { name: '+ Add a Card' })).toBeInTheDocument()
    await user.click(screen.getByRole('link', { name: 'Generate from Notes' }))

    expect(await screen.findByRole('heading', { name: 'Generate Cards from Notes' })).toBeInTheDocument()
    expect(router.state.location.pathname).toBe('/decks/1/generate')
  })

  it('shows how many cards were added under the action row, then clears it from history', async () => {
    mockDeckApi()
    const router = renderApp({ pathname: '/decks/1', state: { addedCount: 3 } })

    const message = await screen.findByText('3 cards added.')
    // Below the action row and above the card count, not under the title
    const generate = screen.getByRole('link', { name: 'Generate from Notes' })
    expect(generate.compareDocumentPosition(message) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy()
    expect(message.compareDocumentPosition(screen.getByText('1 card')) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy()
    // Cleared from history so a reload or Back doesn't show it again; the message stays for now
    await waitFor(() => expect(router.state.location.state).toBeNull())
    expect(screen.getByText('3 cards added.')).toBeInTheDocument()
  })

  it('says "card" for a single added card', async () => {
    mockDeckApi()
    renderApp({ pathname: '/decks/1', state: { addedCount: 1 } })

    expect(await screen.findByText('1 card added.')).toBeInTheDocument()
  })

  it('shows no message on a normal visit', async () => {
    mockDeckApi()
    renderApp('/decks/1')

    await screen.findByRole('heading', { name: 'Biology' })
    expect(screen.queryByText(/added\./)).not.toBeInTheDocument()
  })

  it.each([
    ['opening the add form', '+ Add a Card'],
    ['editing a card', 'Edit'],
    ['deleting a card', 'Delete'],
    ['editing the deck name', 'Edit Deck Name'],
  ])('clears the added-cards message on %s', async (_, buttonName) => {
    vi.spyOn(window, 'confirm').mockReturnValue(true)
    mockDeckApi({ 'DELETE /decks/1/cards/1': jsonResponse(204, undefined) })
    renderApp({ pathname: '/decks/1', state: { addedCount: 3 } })
    const user = userEvent.setup()
    await screen.findByText('3 cards added.')

    await user.click(screen.getByRole('button', { name: buttonName }))

    await waitFor(() => expect(screen.queryByText('3 cards added.')).not.toBeInTheDocument())
  })

  it('clears the added-cards message on clicking Generate, so coming back shows none', async () => {
    mockDeckApi()
    const router = renderApp({ pathname: '/decks/1', state: { addedCount: 3 } })
    const user = userEvent.setup()
    await screen.findByText('3 cards added.')

    await user.click(screen.getByRole('link', { name: 'Generate from Notes' }))
    await screen.findByRole('heading', { name: 'Generate Cards from Notes' })
    await act(() => router.navigate(-1))

    expect(await screen.findByRole('heading', { name: 'Biology' })).toBeInTheDocument()
    expect(screen.queryByText('3 cards added.')).not.toBeInTheDocument()
  })

  it('puts Generate, then Add a card, in one row above the card list', async () => {
    mockDeckApi()
    renderApp('/decks/1')

    const generate = await screen.findByRole('link', { name: 'Generate from Notes' })
    const add = screen.getByRole('button', { name: '+ Add a Card' })
    const count = screen.getByText('1 card')

    expect(generate.parentElement).toBe(add.parentElement)
    expect(generate.compareDocumentPosition(add) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy()
    expect(add.compareDocumentPosition(count) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy()
  })

  it('points to both ways of adding cards on an empty deck', async () => {
    mockDeckApi({ 'GET /decks/1/cards': jsonResponse(200, []) })
    renderApp('/decks/1')

    expect(
      await screen.findByText('This deck has no cards yet. Generate them from your notes, or add one by hand.')
    ).toBeInTheDocument()
  })

  it('says when the deck no longer exists, with a link to the dashboard', async () => {
    mockDeckApi({
      'GET /decks/1': jsonResponse(404, { detail: 'Deck not found' }),
      'GET /decks': jsonResponse(200, []),
    })
    const router = renderApp('/decks/1')
    const user = userEvent.setup()

    expect(await screen.findByText('This deck no longer exists.')).toBeInTheDocument()
    await user.click(screen.getByRole('link', { name: 'Back to Dashboard' }))

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
    ['   ', 'An answer', "Question can't be empty."],
    ['A question', '', "Answer can't be empty."],
    ['', ' \t', "Question can't be empty. Answer can't be empty."],
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

    expect(await screen.findByText("Answer can't be empty.")).toBeInTheDocument()
  })

  it("clears a field's message as soon as that field is typed in", async () => {
    mockDeckApi()
    renderApp('/decks/1')
    const user = userEvent.setup()
    await openAddCardForm(user)
    await user.click(screen.getByRole('button', { name: 'Add Card' }))
    expect(screen.getByText("Question can't be empty. Answer can't be empty.")).toBeInTheDocument()

    await user.type(screen.getByRole('textbox', { name: 'Question' }), 'Q')
    expect(screen.getByText("Answer can't be empty.")).toBeInTheDocument()
    expect(screen.queryByText(/Question can't be empty/)).not.toBeInTheDocument()

    await user.type(screen.getByRole('textbox', { name: 'Answer' }), 'A')
    expect(screen.queryByText(/can't be empty/)).not.toBeInTheDocument()
  })

  it('shows the message on its own line below the fields', async () => {
    mockDeckApi()
    renderApp('/decks/1')
    const user = userEvent.setup()
    await openAddCardForm(user)

    await user.click(screen.getByRole('button', { name: 'Add Card' }))

    const message = screen.getByText("Question can't be empty. Answer can't be empty.")
    const answerBox = screen.getByRole('textbox', { name: 'Answer' })
    expect(answerBox.compareDocumentPosition(message) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy()
  })

  it('opens the form under the row, hiding Add a card but keeping Generate', async () => {
    mockDeckApi()
    renderApp('/decks/1')
    const user = userEvent.setup()

    await openAddCardForm(user)

    expect(screen.queryByRole('button', { name: '+ Add a Card' })).not.toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Generate from Notes' })).toBeInTheDocument()
    expect(screen.getByRole('textbox', { name: 'Question' })).toHaveFocus()
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
    expect(screen.getByText('Card added.')).toBeInTheDocument()
    expect(questionBox).toHaveValue('')
    expect(screen.getByRole('textbox', { name: 'Answer' })).toHaveValue('')
    expect(questionBox).toHaveFocus()
  })

  it('clears "Card added" once the next card is typed', async () => {
    mockDeckApi({ 'POST /decks/1/cards': jsonResponse(201, { card_id: 2, deck_id: 1, question: 'Q2', answer: 'A2' }) })
    renderApp('/decks/1')
    const user = userEvent.setup()
    await openAddCardForm(user)

    await user.type(screen.getByRole('textbox', { name: 'Question' }), 'Q2')
    await user.type(screen.getByRole('textbox', { name: 'Answer' }), 'A2')
    await user.click(screen.getByRole('button', { name: 'Add Card' }))
    await screen.findByText('Card added.')

    await user.keyboard('Q')

    expect(screen.queryByText('Card added.')).not.toBeInTheDocument()
  })

  it('closes the form with Done, clearing "Card added" and returning focus to Add a card', async () => {
    mockDeckApi({ 'POST /decks/1/cards': jsonResponse(201, { card_id: 2, deck_id: 1, question: 'Q2', answer: 'A2' }) })
    renderApp('/decks/1')
    const user = userEvent.setup()
    await openAddCardForm(user)
    await user.type(screen.getByRole('textbox', { name: 'Question' }), 'Q2')
    await user.type(screen.getByRole('textbox', { name: 'Answer' }), 'A2')
    await user.click(screen.getByRole('button', { name: 'Add Card' }))
    await screen.findByText('Card added.')

    expect(screen.queryByRole('button', { name: 'Cancel' })).not.toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Done' }))

    expect(screen.queryByRole('textbox', { name: 'Question' })).not.toBeInTheDocument()
    expect(screen.queryByText('Card added.')).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: '+ Add a Card' })).toHaveFocus()
  })
})

describe('editing a card', () => {
  it.each([
    ['question', "Question can't be empty."],
    ['answer', "Answer can't be empty."],
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

  it("shows both messages below the fields and buttons, clearing each when its field is typed in", async () => {
    mockDeckApi()
    renderApp('/decks/1')
    const user = userEvent.setup()
    await user.click(await screen.findByRole('button', { name: 'Edit' }))
    const [questionBox, answerBox] = screen.getAllByRole('textbox')
    await user.clear(questionBox)
    await user.clear(answerBox)

    await user.click(screen.getByRole('button', { name: 'Save' }))
    const message = screen.getByText("Question can't be empty. Answer can't be empty.")
    // A separate line after the fields and buttons; the CSS gives it the full width
    const cancel = screen.getByRole('button', { name: 'Cancel' })
    expect(cancel.compareDocumentPosition(message) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy()

    await user.type(answerBox, 'A')
    expect(screen.getByText("Question can't be empty.")).toBeInTheDocument()
    expect(screen.queryByText(/Answer can't be empty/)).not.toBeInTheDocument()

    await user.type(questionBox, 'Q')
    expect(screen.queryByText(/can't be empty/)).not.toBeInTheDocument()
  })
})

describe('deleting a card', () => {
  const TWO_CARDS = [CARD, { card_id: 2, deck_id: 1, question: 'Q2', answer: 'A2' }]

  function mockFailedDelete() {
    vi.spyOn(window, 'confirm').mockReturnValue(true)
    return mockDeckApi({
      'GET /decks/1/cards': jsonResponse(200, TWO_CARDS),
      'DELETE /decks/1/cards/2': jsonResponse(500, { detail: 'Server error' }),
    })
  }

  it("shows a failed delete in that card's row, with no edit form open", async () => {
    mockFailedDelete()
    renderApp('/decks/1')
    const user = userEvent.setup()
    await screen.findByText('Q2')
    const [firstRow, secondRow] = screen.getAllByRole('listitem')

    await user.click(within(secondRow).getByRole('button', { name: 'Delete' }))

    expect(await within(secondRow).findByRole('alert')).toHaveTextContent('Server error')
    expect(within(firstRow).queryByRole('alert')).not.toBeInTheDocument()
    expect(screen.queryByRole('textbox')).not.toBeInTheDocument()
    expect(screen.getByText('Q2')).toBeInTheDocument()
  })

  it('clears the delete error on the next action', async () => {
    mockFailedDelete()
    renderApp('/decks/1')
    const user = userEvent.setup()
    await screen.findByText('Q2')
    const secondRow = screen.getAllByRole('listitem')[1]
    await user.click(within(secondRow).getByRole('button', { name: 'Delete' }))
    await screen.findByText('Server error')

    await user.click(screen.getByRole('button', { name: '+ Add a Card' }))

    expect(screen.queryByText('Server error')).not.toBeInTheDocument()
  })
})
