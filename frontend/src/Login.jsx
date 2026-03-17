import { useState } from 'react'
import { GoogleLogin } from '@react-oauth/google'
import { useAuth } from './AuthContext'
import './Login.css'

const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID || ''
const IS_DEV = import.meta.env.DEV

function DevLoginForm({ onLogin }) {
  const [email, setEmail] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await onLogin(email)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} style={{ marginTop: '1rem' }}>
      <p style={{ color: '#f59e0b', fontSize: '0.8rem', marginBottom: '0.5rem' }}>
        ⚠️ Dev mode — no password required
      </p>
      <input
        type="email"
        placeholder="Enter your email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        required
        style={{
          width: '100%',
          padding: '0.5rem',
          marginBottom: '0.5rem',
          borderRadius: '4px',
          border: '1px solid #ccc',
          boxSizing: 'border-box',
        }}
      />
      {error && <p style={{ color: 'red', fontSize: '0.85rem' }}>{error}</p>}
      <button
        type="submit"
        disabled={loading}
        style={{
          width: '100%',
          padding: '0.5rem',
          background: '#4b5563',
          color: 'white',
          border: 'none',
          borderRadius: '4px',
          cursor: 'pointer',
        }}
      >
        {loading ? 'Signing in...' : 'Dev Sign In'}
      </button>
    </form>
  )
}

function Login() {
  const { login, devLogin } = useAuth()

  const handleGoogleSuccess = async (credentialResponse) => {
    try {
      await login(credentialResponse.credential)
    } catch (error) {
      console.error('Login failed:', error)
      alert(`Login failed: ${error.message}`)
    }
  }

  const handleGoogleError = () => {
    console.error('Google login failed')
    alert('Google login failed. Please try again.')
  }

  const noGoogleConfigured = !GOOGLE_CLIENT_ID

  return (
    <div className="login-container">
      <div className="login-card">
        <h1>MyStock</h1>
        <p className="subtitle">LEGO Inventory Management System</p>

        {noGoogleConfigured ? (
          <p className="error-message">
            Google OAuth is not configured. Set VITE_GOOGLE_CLIENT_ID in your environment.
          </p>
        ) : (
          <>
            <p className="description">Sign in with your Google account to continue</p>
            <div className="google-login-wrapper">
              <GoogleLogin
                onSuccess={handleGoogleSuccess}
                onError={handleGoogleError}
                useOneTap={false}
              />
            </div>
          </>
        )}

        {IS_DEV && (
          <DevLoginForm onLogin={devLogin} />
        )}
      </div>
    </div>
  )
}

export default Login
