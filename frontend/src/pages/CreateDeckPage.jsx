import { useState } from 'react'
import { useNavigate } from 'react-router'
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
    </form>
  )
}

export default CreateDeckPage
