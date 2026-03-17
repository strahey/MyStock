import { createContext, useContext, useState, useEffect } from 'react'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

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
  const [isImpersonating, setIsImpersonating] = useState(false)
  const [adminUser, setAdminUser] = useState(null)

  // Load token from localStorage on mount
  useEffect(() => {
    const storedToken = localStorage.getItem('authToken')
    const storedUser = localStorage.getItem('authUser')
    const storedImpersonating = localStorage.getItem('isImpersonating') === 'true'
    const storedAdminUser = localStorage.getItem('adminUser')

    if (storedToken && storedUser) {
      setToken(storedToken)
      try {
        setUser(JSON.parse(storedUser))
      } catch (e) {
        localStorage.removeItem('authToken')
        localStorage.removeItem('authUser')
      }
    }

    if (storedImpersonating && storedAdminUser) {
      setIsImpersonating(true)
      try {
        setAdminUser(JSON.parse(storedAdminUser))
      } catch (e) {
        localStorage.removeItem('isImpersonating')
        localStorage.removeItem('adminUser')
        localStorage.removeItem('adminToken')
        localStorage.removeItem('adminRefreshToken')
      }
    }

    setLoading(false)
  }, [])

  const login = async (googleToken) => {
    const response = await fetch(`${API_BASE_URL}/api/auth/login/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id_token: googleToken }),
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.error || 'Login failed')
    }

    const data = await response.json()
    _applyAuth(data)
    return data
  }

  const devLogin = async (email) => {
    const response = await fetch(`${API_BASE_URL}/api/auth/dev-login/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email }),
    })
    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.error || 'Dev login failed')
    }
    const data = await response.json()
    _applyAuth(data)
    return data
  }

  // Store tokens and user info into state + localStorage
  const _applyAuth = (data) => {
    localStorage.setItem('authToken', data.access)
    localStorage.setItem('authUser', JSON.stringify(data.user))
    localStorage.setItem('refreshToken', data.refresh)
    setToken(data.access)
    setUser(data.user)
  }

  const impersonate = async (targetUserId) => {
    const currentToken = localStorage.getItem('authToken')
    const currentUser = localStorage.getItem('authUser')
    const currentRefresh = localStorage.getItem('refreshToken')

    const response = await fetch(`${API_BASE_URL}/api/auth/impersonate/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${currentToken}`,
      },
      body: JSON.stringify({ user_id: targetUserId }),
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.error || 'Impersonation failed')
    }

    const data = await response.json()

    // Save admin credentials so we can restore them
    localStorage.setItem('adminToken', currentToken)
    localStorage.setItem('adminUser', currentUser)
    localStorage.setItem('adminRefreshToken', currentRefresh)
    localStorage.setItem('isImpersonating', 'true')

    _applyAuth(data)
    setIsImpersonating(true)
    setAdminUser(JSON.parse(currentUser))
  }

  const stopImpersonating = () => {
    const savedToken = localStorage.getItem('adminToken')
    const savedUser = localStorage.getItem('adminUser')
    const savedRefresh = localStorage.getItem('adminRefreshToken')

    localStorage.setItem('authToken', savedToken)
    localStorage.setItem('authUser', savedUser)
    localStorage.setItem('refreshToken', savedRefresh)

    localStorage.removeItem('adminToken')
    localStorage.removeItem('adminUser')
    localStorage.removeItem('adminRefreshToken')
    localStorage.removeItem('isImpersonating')

    setToken(savedToken)
    setUser(JSON.parse(savedUser))
    setIsImpersonating(false)
    setAdminUser(null)
  }

  const logout = () => {
    localStorage.removeItem('authToken')
    localStorage.removeItem('authUser')
    localStorage.removeItem('refreshToken')
    localStorage.removeItem('adminToken')
    localStorage.removeItem('adminUser')
    localStorage.removeItem('adminRefreshToken')
    localStorage.removeItem('isImpersonating')
    setToken(null)
    setUser(null)
    setIsImpersonating(false)
    setAdminUser(null)
  }

  const refreshToken = async () => {
    try {
      const refresh = localStorage.getItem('refreshToken')
      if (!refresh) {
        throw new Error('No refresh token')
      }

      const response = await fetch(`${API_BASE_URL}/api/auth/refresh/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
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
    isImpersonating,
    adminUser,
    login,
    devLogin,
    impersonate,
    stopImpersonating,
    logout,
    refreshToken,
    isAuthenticated: !!token && !!user,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
