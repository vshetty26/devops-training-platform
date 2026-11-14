import { createContext, useContext, useState, useEffect } from 'react'
import PropTypes from 'prop-types'

const AuthContext = createContext(null)

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null)
  const [token, setToken] = useState(localStorage.getItem('token'))
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    checkAuth()
  }, [])

  const checkAuth = async () => {
    const storedToken = localStorage.getItem('token')
    if (storedToken) {
      try {
        const response = await fetch('/api/auth/me', {
          headers: {
            'Authorization': `Bearer ${storedToken}`
          }
        })
        if (response.ok) {
          const userData = await response.json()
          setUser(userData)
          setToken(storedToken)
          setIsAuthenticated(true)
        } else {
          // Token is invalid or expired
          localStorage.removeItem('token')
          setToken(null)
          setUser(null)
          setIsAuthenticated(false)
        }
      } catch (error) {
        console.error('Auth check failed:', error)
        localStorage.removeItem('token')
        setToken(null)
        setUser(null)
        setIsAuthenticated(false)
      }
    }
    setLoading(false)
  }

  const login = async (username, password) => {
    try {
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ username, password })
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        const errorMessage = errorData.detail || 'Login failed. Please check your credentials.'
        throw new Error(errorMessage)
      }

      const data = await response.json()
      
      // Store token and user data
      setToken(data.token)
      setUser(data.user)
      setIsAuthenticated(true)
      localStorage.setItem('token', data.token)
      
      return data
    } catch (error) {
      // Clear any stale data on login failure
      setUser(null)
      setToken(null)
      setIsAuthenticated(false)
      localStorage.removeItem('token')
      throw error
    }
  }

  const logout = () => {
    setUser(null)
    setToken(null)
    setIsAuthenticated(false)
    localStorage.removeItem('token')
  }

  const value = {
    user,
    token,
    isAuthenticated,
    loading,
    login,
    logout,
    checkAuth
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

AuthProvider.propTypes = {
  children: PropTypes.node.isRequired
}
