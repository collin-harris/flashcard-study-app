import { useState } from 'react'
import { Link, useNavigate } from 'react-router'
import { registerUser } from '../api'
import { isValidEmail } from '../validation'
import PasswordInput from '../components/PasswordInput'
import './RegisterPage.css'

function RegisterPage() {
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const navigate = useNavigate()

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')

    if (!isValidEmail(email)) {
      setError('Invalid email')
      return
    }

    try {
      await registerUser(name, email, password)
      navigate('/login')
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-card">
        <form onSubmit={handleSubmit} noValidate>
          <h1>Register</h1>

          <label>
            Name
            <input value={name} onChange={(e) => setName(e.target.value)} />
          </label>

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

          <button type="submit" className="auth-submit">Register</button>
        </form>

        <p className="auth-switch">
          <Link to="/login">Already have an account? Login</Link>
        </p>
      </div>
    </div>
  )
}

export default RegisterPage
