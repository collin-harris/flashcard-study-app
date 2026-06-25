import { useState } from 'react'
import { Link, useNavigate } from 'react-router'
import { createDeck } from '../api'

function CreateDeckPage() {
  const [name, setName] = useState('')
  const [error, setError] = useState('')
  const navigate = useNavigate()

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')

    try {
      await createDeck(name)
      navigate('/dashboard')
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      <h1>Create Deck</h1>

      <label>
        Deck Name
        <input value={name} onChange={(e) => setName(e.target.value)} />
      </label>

      {error && <p>{error}</p>}

      <button type="submit">Create</button>
      <Link to="/dashboard">Cancel</Link>
    </form>
  )
}

export default CreateDeckPage
