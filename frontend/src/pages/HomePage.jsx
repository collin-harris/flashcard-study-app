import { Link } from 'react-router'
import './HomePage.css'

function HomePage() {
  return (
    <div className="auth-page">
      <div className="auth-card">
        <h1>Flashcard Study App</h1>
        <div className="auth-actions">
          <Link to="/login">Login</Link>
          <Link to="/register">Register</Link>
        </div>
      </div>
    </div>
  )
}

export default HomePage
