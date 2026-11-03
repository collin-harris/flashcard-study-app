import { render } from '@testing-library/react'
import { createMemoryRouter, createRoutesFromElements, RouterProvider } from 'react-router'
import { vi } from 'vitest'
import { appRoutes } from '../App.jsx'

// A fake fetch response. A body of undefined makes json() fail, like a
// non-JSON error page.
export function jsonResponse(status, body) {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: () => (body === undefined ? Promise.reject(new SyntaxError('Not JSON')) : Promise.resolve(body)),
  }
}

// Replaces fetch with a stub that answers from `routes`, keyed by
// "METHOD /path". A value is a response, or a function of the parsed request
// body returning one (or a promise of one). Every call is recorded.
export function mockApi(routes) {
  const calls = []
  const fetchMock = vi.fn(async (url, options = {}) => {
    const method = options.method || 'GET'
    const path = new URL(url).pathname
    const body = options.body ? JSON.parse(options.body) : undefined
    calls.push({ method, path, body })

    const handler = routes[`${method} ${path}`]
    if (!handler) {
      throw new Error(`No mock for ${method} ${path}`)
    }
    return typeof handler === 'function' ? handler(body) : handler
  })
  vi.stubGlobal('fetch', fetchMock)
  return calls
}

// Renders the app's real route tree at `path`, logged in
export function renderApp(path) {
  localStorage.setItem('token', 'test-token')
  const router = createMemoryRouter(createRoutesFromElements(appRoutes), { initialEntries: [path] })
  render(<RouterProvider router={router} />)
  return router
}

// A promise to resolve by hand, for requests that should stay in flight
export function deferred() {
  let resolve
  const promise = new Promise((res) => {
    resolve = res
  })
  return { promise, resolve }
}
