import { Link, useNavigate } from 'react-router'
import { clearToken } from '../api'
import './Header.css'

function Header() {
  const navigate = useNavigate()

  function handleLogout() {
    clearToken()
    navigate('/login')
  }

  return (
    <header className="app-header">
      <Link to="/dashboard" className="app-header__brand">Flashcard Study App</Link>
      <button onClick={handleLogout} className="app-header__logout">Logout</button>
    </header>
  )
}

export default Header
