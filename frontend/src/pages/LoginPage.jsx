import { useState, useEffect } from 'react'
import { Link, useLocation, useNavigate } from 'react-router'
import { clearToken, loginUser, saveToken } from '../api'
import { isValidEmail } from '../validation'
import PasswordInput from '../components/PasswordInput'
import './LoginPage.css'

function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const navigate = useNavigate()
  const location = useLocation()

  // Logout navigates here and leaves clearing the token to this page
  useEffect(() => {
    if (location.state?.loggedOut) {
      clearToken()
    }
  }, [location.state])

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')

    if (!isValidEmail(email)) {
      setError('Enter a valid email address.')
      return
    }

    try {
      const data = await loginUser(email, password)
      saveToken(data.access_token)
      navigate('/dashboard')
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-card">
        <form onSubmit={handleSubmit} noValidate>
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
            <PasswordInput value={password} onChange={(e) => setPassword(e.target.value)} />
          </label>

          {error && <p className="auth-error">{error}</p>}

          <button type="submit" className="auth-submit">Login</button>
        </form>

        <p className="auth-switch">
          <Link to="/register">Don't have an account? Register</Link>
        </p>
      </div>
    </div>
  )
}

export default LoginPage
