import { createContext, useContext, useState, useEffect } from 'react'

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
  const [token, setToken] = useState(null)
  const [loading, setLoading] = useState(true)

  // Load token from localStorage on mount
  useEffect(() => {
    const storedToken = localStorage.getItem('authToken')
    const storedUser = localStorage.getItem('authUser')
    
    if (storedToken && storedUser) {
      setToken(storedToken)
      try {
        setUser(JSON.parse(storedUser))
      } catch (e) {
        console.error('Failed to parse stored user:', e)
        localStorage.removeItem('authToken')
        localStorage.removeItem('authUser')
      }
    }
    setLoading(false)
  }, [])

  const login = async (googleToken) => {
    try {
      // Exchange Google token for JWT
      const response = await fetch('http://localhost:8888/api/auth/login/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ id_token: googleToken }),
      })

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.error || 'Login failed')
      }

      const data = await response.json()
      
      // Store tokens and user info
      localStorage.setItem('authToken', data.access)
      localStorage.setItem('authUser', JSON.stringify(data.user))
      localStorage.setItem('refreshToken', data.refresh)
      
      setToken(data.access)
      setUser(data.user)
      
      return data
    } catch (error) {
      console.error('Login error:', error)
      throw error
    }
  }

  const logout = () => {
    localStorage.removeItem('authToken')
    localStorage.removeItem('authUser')
    localStorage.removeItem('refreshToken')
    setToken(null)
    setUser(null)
  }

  const refreshToken = async () => {
    try {
      const refresh = localStorage.getItem('refreshToken')
      if (!refresh) {
        throw new Error('No refresh token')
      }

      const response = await fetch('http://localhost:8000/api/auth/refresh/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ refresh }),
      })

      if (!response.ok) {
        throw new Error('Token refresh failed')
      }

      const data = await response.json()
      localStorage.setItem('authToken', data.access)
      setToken(data.access)
      
      return data.access
    } catch (error) {
      console.error('Token refresh error:', error)
      logout()
      throw error
    }
  }

  const value = {
    user,
    token,
    loading,
    login,
    logout,
    refreshToken,
    isAuthenticated: !!token && !!user,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

