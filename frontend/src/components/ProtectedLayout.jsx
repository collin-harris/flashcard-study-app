import { Outlet } from 'react-router'
import ProtectedRoute from './ProtectedRoute'
import Header from './Header'

function ProtectedLayout() {
  return (
    <ProtectedRoute>
      <Header />
      <Outlet />
    </ProtectedRoute>
  )
}

export default ProtectedLayout
