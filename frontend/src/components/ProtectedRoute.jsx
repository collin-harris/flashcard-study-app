import { Navigate } from 'react-router'
import { getToken } from '../api'

function ProtectedRoute({ children }) {
  const token = getToken()

  if (!token) {
    return <Navigate to="/login" />
  }

  return children
}

export default ProtectedRoute
