import { Link, useNavigate } from 'react-router'
import './Header.css'

function Header() {
  const navigate = useNavigate()

  // The login page clears the token once it's reached. Clearing it here
  // would log the user out even when a page blocks the navigation and they
  // choose to stay.
  function handleLogout() {
    navigate('/login', { replace: true, state: { loggedOut: true } })
  }

  return (
    <header className="app-header">
      <Link to="/dashboard" className="app-header__brand">Flashcard Study App</Link>
      <button onClick={handleLogout} className="app-header__logout">Logout</button>
    </header>
  )
}

export default Header
