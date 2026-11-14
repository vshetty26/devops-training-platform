import { Navigate, useLocation } from 'react-router-dom'
import PropTypes from 'prop-types'
import { useAuth } from '../context/AuthContext'

/**
 * ProtectedRoute Component
 * 
 * Enforces authentication for protected pages.
 * Redirects unauthenticated users to login page.
 * 
 * Requirements:
 * - 1.4: Platform SHALL restrict access to challenge pages when user is not authenticated
 */
const ProtectedRoute = ({ children }) => {
  const { isAuthenticated, loading } = useAuth()
  const location = useLocation()

  // Show loading state while checking authentication
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-100">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-600">Verifying authentication...</p>
        </div>
      </div>
    )
  }

  // Redirect to login if not authenticated
  if (!isAuthenticated) {
    // Save the location they were trying to access
    return <Navigate to="/" state={{ from: location }} replace />
  }

  // Render protected content
  return children
}

ProtectedRoute.propTypes = {
  children: PropTypes.node.isRequired
}

export default ProtectedRoute
