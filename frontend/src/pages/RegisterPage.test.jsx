import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import { jsonResponse, mockApi, renderApp } from '../test/helpers'

const TOO_LONG = 'Password is too long. Use at most 72 characters, or fewer if it includes emoji or accented letters.'

function renderRegister() {
  const router = renderApp('/register')
  const user = userEvent.setup()
  return { router, user }
}

async function fillIn(user, { name = 'Ada Lovelace', email = 'ada@example.com', password = 'testpass123' } = {}) {
  if (name) await user.type(screen.getByRole('textbox', { name: 'Name' }), name)
  if (email) await user.type(screen.getByRole('textbox', { name: 'Email' }), email)
  // The password box isn't a textbox role while hidden
  if (password) {
    await user.click(screen.getByLabelText('Password', { selector: 'input' }))
    await user.paste(password)
  }
  await user.click(screen.getByRole('button', { name: 'Register' }))
}

describe('RegisterPage', () => {
  it.each([
    ['an empty name', { name: '   ' }, "Name can't be empty."],
    ['a short password', { password: 'seven77' }, 'Password must be at least 8 characters.'],
    ['a password over 72 bytes', { password: 'x'.repeat(73) }, TOO_LONG],
    ['37 accented letters (74 bytes)', { password: 'é'.repeat(37) }, TOO_LONG],
  ])('checks %s before sending anything', async (_, fields, message) => {
    const calls = mockApi({})
    const { user } = renderRegister()

    await fillIn(user, fields)

    expect(screen.getByText(message)).toBeInTheDocument()
    expect(calls).toHaveLength(0)
  })

  it('shows every problem at once, as full sentences', async () => {
    const calls = mockApi({})
    const { user } = renderRegister()

    await fillIn(user, { name: '', email: 'not-an-email', password: 'short' })

    expect(
      screen.getByText("Name can't be empty. Enter a valid email address. Password must be at least 8 characters.")
    ).toBeInTheDocument()
    expect(calls).toHaveLength(0)
  })

  it('accepts a password of 72 bytes made of 36 accented letters', async () => {
    const calls = mockApi({ 'POST /auth/register': jsonResponse(201, { user_id: 1, name: 'Ada', email: 'ada@example.com' }) })
    const { router, user } = renderRegister()

    await fillIn(user, { password: 'é'.repeat(36) })

    await waitFor(() => expect(router.state.location.pathname).toBe('/login'))
    expect(calls[0].body).toEqual({ name: 'Ada Lovelace', email: 'ada@example.com', password: 'é'.repeat(36) })
  })

  it("shows the API's validation messages as they are", async () => {
    mockApi({
      'POST /auth/register': jsonResponse(422, {
        detail: [
          { type: 'empty_text', loc: ['body', 'name'], msg: "Name can't be empty." },
          { type: 'password_too_short', loc: ['body', 'password'], msg: 'Password must be at least 8 characters.' },
        ],
      }),
    })
    const { user } = renderRegister()

    await fillIn(user)

    expect(
      await screen.findByText("Name can't be empty. Password must be at least 8 characters.")
    ).toBeInTheDocument()
  })
})
