import { useState, useEffect } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

const Login = () => {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [validationErrors, setValidationErrors] = useState({})
  const { login, isAuthenticated, loading } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  // Redirect if already authenticated
  useEffect(() => {
    if (!loading && isAuthenticated) {
      const from = location.state?.from?.pathname || '/challenges'
      navigate(from, { replace: true })
    }
  }, [isAuthenticated, loading, navigate, location])

  const validateForm = () => {
    const errors = {}
    
    if (!username.trim()) {
      errors.username = 'Username is required'
    } else if (username.length < 3) {
      errors.username = 'Username must be at least 3 characters'
    }
    
    if (!password) {
      errors.password = 'Password is required'
    } else if (password.length < 6) {
      errors.password = 'Password must be at least 6 characters'
    }
    
    setValidationErrors(errors)
    return Object.keys(errors).length === 0
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setValidationErrors({})
    
    // Client-side validation
    if (!validateForm()) {
      return
    }
    
    setIsLoading(true)
    
    try {
      await login(username, password)
      // Navigation is handled by useEffect above
    } catch (err) {
      setError(err.message || 'Login failed. Please check your credentials.')
    } finally {
      setIsLoading(false)
    }
  }

  const handleUsernameChange = (e) => {
    setUsername(e.target.value)
    // Clear validation error when user starts typing
    if (validationErrors.username) {
      setValidationErrors(prev => ({ ...prev, username: '' }))
    }
  }

  const handlePasswordChange = (e) => {
    setPassword(e.target.value)
    // Clear validation error when user starts typing
    if (validationErrors.password) {
      setValidationErrors(prev => ({ ...prev, password: '' }))
    }
  }

  // Show loading state while checking authentication
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-100">
        <div className="text-gray-600">Loading...</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100">
      <div className="bg-white p-8 rounded-lg shadow-md w-96">
        <h1 className="text-3xl font-bold mb-2 text-center text-blue-600">DevOps Arena</h1>
        <p className="text-gray-600 text-center mb-6 text-sm">
          Practice troubleshooting real-world incidents
        </p>
        
        <form onSubmit={handleSubmit} noValidate>
          <div className="mb-4">
            <label 
              htmlFor="username" 
              className="block text-gray-700 text-sm font-bold mb-2"
            >
              Username
            </label>
            <input
              id="username"
              type="text"
              value={username}
              onChange={handleUsernameChange}
              className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 transition-colors ${
                validationErrors.username 
                  ? 'border-red-500 focus:ring-red-500' 
                  : 'border-gray-300 focus:ring-blue-500'
              }`}
              disabled={isLoading}
              required
              autoComplete="username"
              aria-invalid={!!validationErrors.username}
              aria-describedby={validationErrors.username ? 'username-error' : undefined}
            />
            {validationErrors.username && (
              <p id="username-error" className="mt-1 text-red-500 text-xs">
                {validationErrors.username}
              </p>
            )}
          </div>
          
          <div className="mb-6">
            <label 
              htmlFor="password" 
              className="block text-gray-700 text-sm font-bold mb-2"
            >
              Password
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={handlePasswordChange}
              className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 transition-colors ${
                validationErrors.password 
                  ? 'border-red-500 focus:ring-red-500' 
                  : 'border-gray-300 focus:ring-blue-500'
              }`}
              disabled={isLoading}
              required
              autoComplete="current-password"
              aria-invalid={!!validationErrors.password}
              aria-describedby={validationErrors.password ? 'password-error' : undefined}
            />
            {validationErrors.password && (
              <p id="password-error" className="mt-1 text-red-500 text-xs">
                {validationErrors.password}
              </p>
            )}
          </div>
          
          {error && (
            <div 
              className="mb-4 p-3 bg-red-50 border border-red-300 rounded-md text-red-700 text-sm"
              role="alert"
            >
              {error}
            </div>
          )}
          
          <button
            type="submit"
            disabled={isLoading}
            className={`w-full py-2 px-4 rounded-md text-white font-semibold transition-colors ${
              isLoading 
                ? 'bg-gray-400 cursor-not-allowed' 
                : 'bg-blue-500 hover:bg-blue-600'
            }`}
          >
            {isLoading ? 'Logging in...' : 'Login'}
          </button>
        </form>
        
        <div className="mt-6 text-center text-sm text-gray-600">
          <p>Demo Account: <span className="font-mono text-blue-600">demo / demo123</span></p>
        </div>
      </div>
    </div>
  )
}

export default Login
