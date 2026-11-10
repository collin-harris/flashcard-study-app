import { act, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import { jsonResponse, mockApi, renderApp } from '../test/helpers'

describe('Header', () => {
  it('logs out and replaces the current page in history', async () => {
    mockApi({ 'GET /decks': jsonResponse(200, []) })
    const router = renderApp(['/', '/dashboard'])
    const user = userEvent.setup()

    await user.click(within(screen.getByRole('banner')).getByRole('button', { name: 'Logout' }))
    await waitFor(() => expect(router.state.location.pathname).toBe('/login'))
    await waitFor(() => expect(localStorage.getItem('token')).toBeNull())

    // Back goes past the dashboard, which would only redirect to login now
    await act(() => router.navigate(-1))

    expect(router.state.location.pathname).toBe('/')
  })
})
