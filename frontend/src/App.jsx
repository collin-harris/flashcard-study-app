import { Routes, Route } from 'react-router'
import RegisterPage from './pages/RegisterPage'
import LoginPage from './pages/LoginPage'
import DashboardPage from './pages/DashboardPage'
import CreateDeckPage from './pages/CreateDeckPage'
import DeckDetailPage from './pages/DeckDetailPage'
import ProtectedRoute from './components/ProtectedRoute'

function App() {
  return (
    <Routes>
      <Route path="/" element={<h1>Flashcard Study App</h1>} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <DashboardPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/decks/new"
        element={
          <ProtectedRoute>
            <CreateDeckPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/decks/:deckId"
        element={
          <ProtectedRoute>
            <DeckDetailPage />
          </ProtectedRoute>
        }
      />
    </Routes>
  )
}

export default App
