import { Route } from 'react-router'
import HomePage from './pages/HomePage'
import RegisterPage from './pages/RegisterPage'
import LoginPage from './pages/LoginPage'
import DashboardPage from './pages/DashboardPage'
import CreateDeckPage from './pages/CreateDeckPage'
import DeckDetailPage from './pages/DeckDetailPage'
import StudySessionPage from './pages/StudySessionPage'
import GenerateCardsPage from './pages/GenerateCardsPage'
import ProtectedLayout from './components/ProtectedLayout'

// The route tree, turned into a data router in main.jsx (and into a memory
// router in tests). A data router is what lets a page block navigation while
// it has unsaved work.
export const appRoutes = (
  <>
    <Route path="/" element={<HomePage />} />
    <Route path="/register" element={<RegisterPage />} />
    <Route path="/login" element={<LoginPage />} />

    <Route element={<ProtectedLayout />}>
      <Route path="/dashboard" element={<DashboardPage />} />
      <Route path="/decks/new" element={<CreateDeckPage />} />
      <Route path="/decks/:deckId" element={<DeckDetailPage />} />
      <Route path="/decks/:deckId/generate" element={<GenerateCardsPage />} />
      <Route path="/decks/:deckId/study/:mode" element={<StudySessionPage />} />
    </Route>
  </>
)
