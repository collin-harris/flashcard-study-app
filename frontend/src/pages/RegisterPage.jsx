import { useState } from 'react'
import { useNavigate } from 'react-router'
import { registerUser } from '../api'

function RegisterPage() {
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const navigate = useNavigate()

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')

    try {
      await registerUser(name, email, password)
      navigate('/login')
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <form onSubmit={handleSubmit}>
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
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
      </label>

      {error && <p>{error}</p>}

      <button type="submit">Register</button>
    </form>
  )
}

export default RegisterPage
