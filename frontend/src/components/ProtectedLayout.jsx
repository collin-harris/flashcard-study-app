import { Outlet } from 'react-router'
import ProtectedRoute from './ProtectedRoute'
import Header from './Header'
import './ProtectedLayout.css'

function ProtectedLayout() {
  return (
    <ProtectedRoute>
      <Header />
      <main className="page-container">
        <Outlet />
      </main>
    </ProtectedRoute>
  )
}

export default ProtectedLayout
