import { Routes, Route, Link } from 'react-router'
import RegisterPage from './pages/RegisterPage'
import LoginPage from './pages/LoginPage'
import DashboardPage from './pages/DashboardPage'
import CreateDeckPage from './pages/CreateDeckPage'
import DeckDetailPage from './pages/DeckDetailPage'
import StudySessionPage from './pages/StudySessionPage'
import ProtectedLayout from './components/ProtectedLayout'

function App() {
  return (
    <Routes>
      <Route
        path="/"
        element={
          <>
            <h1>Flashcard Study App</h1>
            <Link to="/login">Login</Link>
            <Link to="/register">Register</Link>
          </>
        }
      />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/login" element={<LoginPage />} />

      <Route element={<ProtectedLayout />}>
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/decks/new" element={<CreateDeckPage />} />
        <Route path="/decks/:deckId" element={<DeckDetailPage />} />
        <Route path="/decks/:deckId/study/:mode" element={<StudySessionPage />} />
      </Route>
    </Routes>
  )
}

export default App
