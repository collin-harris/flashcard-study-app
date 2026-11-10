import { act, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { deferred, jsonResponse, mockApi, renderApp } from '../test/helpers'

const DECK = { deck_id: 1, user_id: 1, name: 'Biology' }
const WAIT_MESSAGE = 'Generating cards. This usually takes 10 to 20 seconds.'
const LEAVE_MESSAGE = "Leave this page? Your generated cards haven't been saved and will be lost."

function card(n) {
  return { question: `Question ${n}`, answer: `Answer ${n}`, source: [`Excerpt ${n}`] }
}

function cards(count, start = 1) {
  return Array.from({ length: count }, (_, i) => card(start + i))
}

function generated(cardList, remaining = 2) {
  return jsonResponse(200, { status: 'ok', cards: cardList, remaining })
}

// Answers each call with the next response, repeating the last one
function sequence(...responses) {
  let index = 0
  return () => responses[Math.min(index++, responses.length - 1)]
}

// `history` is the list of entries to start with, ending on the generate page
async function loadPage(routes = {}, history = ['/decks/1/generate']) {
  const calls = mockApi({
    'GET /decks/1': jsonResponse(200, DECK),
    'GET /generations/remaining': jsonResponse(200, { remaining: 3, limit: 5 }),
    'GET /decks/1/cards': jsonResponse(200, []),
    ...routes,
  })
  const router = renderApp(history)
  const user = userEvent.setup()
  await screen.findByRole('heading', { name: 'Generate Cards from Notes' })
  return { calls, router, user }
}

function notesBox() {
  return screen.getByRole('textbox', { name: 'Paste your notes' })
}

function generateButton() {
  return screen.getByRole('button', { name: /^Generat/ })
}

async function enterNotes(user, text) {
  await user.clear(notesBox())
  await user.click(notesBox())
  await user.paste(text)
}

async function generateFrom(user, text = 'Mitochondria produce ATP.') {
  await enterNotes(user, text)
  await user.click(generateButton())
}

function countCalls(calls, method, path) {
  return calls.filter((call) => call.method === method && call.path === path).length
}

describe('notes input', () => {
  it('shows the remaining count next to Generate and an empty character counter', async () => {
    await loadPage()

    const actions = generateButton().parentElement
    expect(await within(actions).findByText('3 of 5 generations left')).toBeInTheDocument()
    expect(screen.getByText('0 / 2,000 characters')).toBeInTheDocument()
    expect(generateButton()).toBeDisabled()
  })

  it('disables Generate for whitespace-only or over-long notes, counting as the API does', async () => {
    const { user } = await loadPage()
    await screen.findByText('3 of 5 generations left')

    await enterNotes(user, '   \n\t ')
    expect(screen.getByText('0 / 2,000 characters')).toBeInTheDocument()
    expect(generateButton()).toBeDisabled()

    await enterNotes(user, 'a'.repeat(2001))
    expect(screen.getByText('2,001 / 2,000 characters')).toBeInTheDocument()
    expect(generateButton()).toBeDisabled()

    // Surrounding whitespace isn't counted, as the API strips it
    await enterNotes(user, `  ${'a'.repeat(2000)}\n`)
    expect(screen.getByText('2,000 / 2,000 characters')).toBeInTheDocument()
    expect(generateButton()).toBeEnabled()
  })

  it('disables Generate when no generations remain', async () => {
    const { user } = await loadPage({
      'GET /generations/remaining': jsonResponse(200, { remaining: 0, limit: 5 }),
    })
    await screen.findByText('0 of 5 generations left')

    await enterNotes(user, 'Some notes')

    expect(generateButton()).toBeDisabled()
    expect(screen.getByText(/You have no generations left/)).toBeInTheDocument()
  })

  it('still allows generating when the remaining count fails to load', async () => {
    const { user } = await loadPage({
      'GET /generations/remaining': jsonResponse(500, { detail: 'Server error' }),
    })

    const actions = generateButton().parentElement
    expect(await within(actions).findByText("Couldn't load your remaining generations.")).toBeInTheDocument()
    await enterNotes(user, 'Some notes')
    expect(generateButton()).toBeEnabled()
  })
})

describe('generating', () => {
  it('sends one request for a double click and shows the wait message', async () => {
    const pending = deferred()
    const { calls, user } = await loadPage({ 'POST /decks/1/cards/generate': () => pending.promise })

    await enterNotes(user, 'Some notes')
    await user.dblClick(generateButton())

    expect(countCalls(calls, 'POST', '/decks/1/cards/generate')).toBe(1)
    expect(screen.getByText(WAIT_MESSAGE)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Generating...' })).toBeDisabled()

    pending.resolve(generated([card(1)]))
    expect(await screen.findByRole('button', { name: 'Save 1 card' })).toBeInTheDocument()
  })

  it('shows the generated cards and their sources for review, and updates the remaining count', async () => {
    const { calls, user } = await loadPage({ 'POST /decks/1/cards/generate': generated(cards(2), 2) })

    await generateFrom(user, 'Mitochondria produce ATP.')

    expect(await screen.findByRole('heading', { name: 'Review 2 cards' })).toBeInTheDocument()
    const questions = screen.getAllByRole('textbox', { name: 'Question' })
    const answers = screen.getAllByRole('textbox', { name: 'Answer' })
    expect(questions.map((box) => box.value)).toEqual(['Question 1', 'Question 2'])
    expect(answers.map((box) => box.value)).toEqual(['Answer 1', 'Answer 2'])
    expect(screen.getByText('Excerpt 1')).toBeInTheDocument()
    expect(screen.getByText('Excerpt 2')).toBeInTheDocument()
    expect(screen.getByText('2 of 5 generations left')).toBeInTheDocument()
    expect(calls.find((call) => call.method === 'POST').body).toEqual({ notes: 'Mitochondria produce ATP.' })
  })

  it('clears the notes after a successful generation', async () => {
    const { user } = await loadPage({ 'POST /decks/1/cards/generate': generated(cards(1)) })

    await generateFrom(user, 'Mitochondria produce ATP.')

    await screen.findByRole('heading', { name: 'Review 1 card' })
    expect(notesBox()).toHaveValue('')
    expect(screen.getByText('0 / 2,000 characters')).toBeInTheDocument()
  })

  it('appends a second generation below the existing drafts', async () => {
    const { user } = await loadPage({
      'POST /decks/1/cards/generate': sequence(generated(cards(2, 1), 2), generated(cards(1, 3), 1)),
    })

    await generateFrom(user, 'First notes')
    await screen.findByRole('heading', { name: 'Review 2 cards' })
    await generateFrom(user, 'Second notes')

    expect(await screen.findByRole('heading', { name: 'Review 3 cards' })).toBeInTheDocument()
    const questions = screen.getAllByRole('textbox', { name: 'Question' }).map((box) => box.value)
    expect(questions).toEqual(['Question 1', 'Question 2', 'Question 3'])
    expect(screen.getByText('1 of 5 generations left')).toBeInTheDocument()
  })

  it('shows the reason for a rejection and keeps the notes', async () => {
    const { user } = await loadPage({
      'POST /decks/1/cards/generate': jsonResponse(200, {
        status: 'rejected',
        reason: "These notes don't contain study material.",
        remaining: 2,
      }),
    })

    await generateFrom(user, 'Buy milk')

    expect(await screen.findByText("These notes don't contain study material.")).toBeInTheDocument()
    expect(screen.getByText('No cards were generated.')).toBeInTheDocument()
    expect(notesBox()).toHaveValue('Buy milk')
    expect(screen.getByText('2 of 5 generations left')).toBeInTheDocument()
    expect(screen.queryByRole('heading', { name: /^Review/ })).not.toBeInTheDocument()
  })

  it.each([
    [429, "You've used all 5 of your card generations for the last 24 hours. Please try again later."],
    [502, "Couldn't generate cards. Please try again."],
    [503, 'Card generation is temporarily unavailable. Please try again in a few minutes.'],
    [500, "Card generation isn't available right now."],
  ])('shows the API message for a %i, keeps the notes, and reloads the remaining count', async (status, detail) => {
    const { calls, user } = await loadPage({
      'GET /generations/remaining': sequence(
        jsonResponse(200, { remaining: 3, limit: 5 }),
        jsonResponse(200, { remaining: 2, limit: 5 })
      ),
      'POST /decks/1/cards/generate': jsonResponse(status, { detail }),
    })
    await screen.findByText('3 of 5 generations left')

    await generateFrom(user, 'Some notes')

    expect(await screen.findByText(detail)).toBeInTheDocument()
    expect(notesBox()).toHaveValue('Some notes')
    expect(await screen.findByText('2 of 5 generations left')).toBeInTheDocument()
    expect(countCalls(calls, 'GET', '/generations/remaining')).toBe(2)
  })
})

describe('reviewing and saving', () => {
  it('removes a card and updates the Save button', async () => {
    const { user } = await loadPage({ 'POST /decks/1/cards/generate': generated(cards(2)) })
    await generateFrom(user)
    await screen.findByRole('button', { name: 'Save 2 cards' })

    await user.click(screen.getAllByRole('button', { name: 'Remove' })[0])

    expect(screen.getByRole('button', { name: 'Save 1 card' })).toBeEnabled()
    expect(screen.getAllByRole('textbox', { name: 'Question' }).map((box) => box.value)).toEqual(['Question 2'])
  })

  it('removes the Save button once no cards remain', async () => {
    const { user } = await loadPage({ 'POST /decks/1/cards/generate': generated(cards(1)) })
    await generateFrom(user)
    await screen.findByRole('button', { name: 'Save 1 card' })

    await user.click(screen.getByRole('button', { name: 'Remove' }))

    expect(screen.queryByRole('button', { name: /^Save/ })).not.toBeInTheDocument()
  })

  it('disables Save while any card has an empty or whitespace-only field', async () => {
    const { user } = await loadPage({ 'POST /decks/1/cards/generate': generated(cards(2)) })
    await generateFrom(user)
    const save = await screen.findByRole('button', { name: 'Save 2 cards' })
    const firstAnswer = screen.getAllByRole('textbox', { name: 'Answer' })[0]

    await user.clear(firstAnswer)
    expect(save).toBeDisabled()
    expect(screen.getByText('Every card needs a question and an answer.')).toBeInTheDocument()

    await user.type(firstAnswer, '   ')
    expect(save).toBeDisabled()

    await user.type(firstAnswer, 'Fixed')
    expect(save).toBeEnabled()
  })

  it('disables Save above 100 cards and says to remove some', async () => {
    const { user } = await loadPage({ 'POST /decks/1/cards/generate': generated(cards(101)) })
    await generateFrom(user)

    const save = await screen.findByRole('button', { name: 'Save 101 cards' })
    expect(save).toBeDisabled()
    expect(
      screen.getByText('You can save at most 100 cards at once. Remove at least 1 to continue.')
    ).toBeInTheDocument()

    await user.click(screen.getAllByRole('button', { name: 'Remove' })[0])

    expect(screen.getByRole('button', { name: 'Save 100 cards' })).toBeEnabled()
    expect(screen.queryByText(/You can save at most 100 cards/)).not.toBeInTheDocument()
  })

  it('saves the edited cards and returns to the deck with a confirmation', async () => {
    const confirm = vi.spyOn(window, 'confirm')
    const { calls, router, user } = await loadPage({
      'POST /decks/1/cards/generate': generated(cards(2)),
      'POST /decks/1/cards/bulk': jsonResponse(201, []),
    })
    await generateFrom(user)
    const firstQuestion = (await screen.findAllByRole('textbox', { name: 'Question' }))[0]
    await user.clear(firstQuestion)
    await user.type(firstQuestion, 'Edited question')

    await user.click(screen.getByRole('button', { name: 'Save 2 cards' }))

    expect(await screen.findByText('Added 2 cards to this deck.')).toBeInTheDocument()
    expect(router.state.location.pathname).toBe('/decks/1')
    expect(confirm).not.toHaveBeenCalled()
    expect(calls.find((call) => call.path === '/decks/1/cards/bulk').body).toEqual({
      cards: [
        { question: 'Edited question', answer: 'Answer 1' },
        { question: 'Question 2', answer: 'Answer 2' },
      ],
    })
  })

  it('replaces the generate page in history after saving', async () => {
    const { router, user } = await loadPage(
      {
        'POST /decks/1/cards/generate': generated(cards(1)),
        'POST /decks/1/cards/bulk': jsonResponse(201, []),
      },
      ['/decks/1', '/decks/1/generate']
    )
    await generateFrom(user)
    await user.click(await screen.findByRole('button', { name: 'Save 1 card' }))
    await screen.findByText('Added 1 card to this deck.')

    // Back skips the finished generate page
    await act(() => router.navigate(-1))

    expect(router.state.location.pathname).toBe('/decks/1')
  })

  it('keeps the drafts and shows the error when saving fails', async () => {
    const { router, user } = await loadPage({
      'POST /decks/1/cards/generate': generated(cards(1)),
      'POST /decks/1/cards/bulk': jsonResponse(503, { detail: 'Service unavailable' }),
    })
    await generateFrom(user)

    await user.click(await screen.findByRole('button', { name: 'Save 1 card' }))

    expect(await screen.findByText('Service unavailable')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Save 1 card' })).toBeEnabled()
    expect(router.state.location.pathname).toBe('/decks/1/generate')
  })
})

describe('leaving with unsaved work', () => {
  it('asks before leaving with unsaved drafts, and stays if the user cancels', async () => {
    const confirm = vi.spyOn(window, 'confirm').mockReturnValue(false)
    const { router, user } = await loadPage({ 'POST /decks/1/cards/generate': generated(cards(1)) })
    await generateFrom(user)
    await screen.findByRole('button', { name: 'Save 1 card' })

    await user.click(screen.getByRole('link', { name: 'Back to Biology' }))

    expect(confirm).toHaveBeenCalledWith(LEAVE_MESSAGE)
    expect(router.state.location.pathname).toBe('/decks/1/generate')
    expect(screen.getByRole('button', { name: 'Save 1 card' })).toBeInTheDocument()

    confirm.mockReturnValue(true)
    await user.click(screen.getByRole('link', { name: 'Back to Biology' }))

    await waitFor(() => expect(router.state.location.pathname).toBe('/decks/1'))
  })

  it('asks before leaving while a generation is in flight', async () => {
    const confirm = vi.spyOn(window, 'confirm').mockReturnValue(false)
    const pending = deferred()
    const { router, user } = await loadPage({ 'POST /decks/1/cards/generate': () => pending.promise })
    await generateFrom(user)

    await user.click(screen.getByRole('link', { name: 'Back to Biology' }))

    expect(confirm).toHaveBeenCalledWith(LEAVE_MESSAGE)
    expect(router.state.location.pathname).toBe('/decks/1/generate')

    pending.resolve(generated([card(1)]))
    await screen.findByRole('button', { name: 'Save 1 card' })
  })

  it('leaves without asking when there is nothing unsaved', async () => {
    const confirm = vi.spyOn(window, 'confirm')
    const { router, user } = await loadPage()

    await user.click(screen.getByRole('link', { name: 'Back to Biology' }))

    await waitFor(() => expect(router.state.location.pathname).toBe('/decks/1'))
    expect(confirm).not.toHaveBeenCalled()
  })

  it('keeps the user logged in when they cancel leaving through Logout', async () => {
    const confirm = vi.spyOn(window, 'confirm').mockReturnValue(false)
    const { router, user } = await loadPage({ 'POST /decks/1/cards/generate': generated(cards(1)) })
    await generateFrom(user)
    await screen.findByRole('button', { name: 'Save 1 card' })
    const logout = within(screen.getByRole('banner')).getByRole('button', { name: 'Logout' })

    await user.click(logout)

    expect(confirm).toHaveBeenCalledWith(LEAVE_MESSAGE)
    expect(localStorage.getItem('token')).toBe('test-token')
    expect(router.state.location.pathname).toBe('/decks/1/generate')

    confirm.mockReturnValue(true)
    await user.click(logout)

    await waitFor(() => expect(router.state.location.pathname).toBe('/login'))
    await waitFor(() => expect(localStorage.getItem('token')).toBeNull())
  })

  it('warns before unloading only while there are unsaved drafts', async () => {
    const { user } = await loadPage({ 'POST /decks/1/cards/generate': generated(cards(1)) })

    const before = new Event('beforeunload', { cancelable: true })
    window.dispatchEvent(before)
    expect(before.defaultPrevented).toBe(false)

    await generateFrom(user)
    await screen.findByRole('button', { name: 'Save 1 card' })

    const after = new Event('beforeunload', { cancelable: true })
    window.dispatchEvent(after)
    expect(after.defaultPrevented).toBe(true)
  })
})
