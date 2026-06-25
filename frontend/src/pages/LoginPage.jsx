import { useState } from 'react'
import { Link, useNavigate } from 'react-router'
import { loginUser, saveToken } from '../api'

function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const navigate = useNavigate()

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')

    try {
      const data = await loginUser(email, password)
      saveToken(data.access_token)
      navigate('/dashboard')
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <>
      <form onSubmit={handleSubmit}>
        <h1>Login</h1>

        <label>
          Email
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </label>

        <label>
          Password
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </label>

        {error && <p>{error}</p>}

        <button type="submit">Login</button>
      </form>

      <Link to="/register">Don't have an account? Register</Link>
    </>
  )
}

export default LoginPage
