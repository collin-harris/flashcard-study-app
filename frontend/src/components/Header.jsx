import { Link, useNavigate } from 'react-router'
import { clearToken } from '../api'

function Header() {
  const navigate = useNavigate()

  function handleLogout() {
    clearToken()
    navigate('/login')
  }

  return (
    <header>
      <Link to="/dashboard">Dashboard</Link>
      <button onClick={handleLogout}>Logout</button>
    </header>
  )
}

export default Header
