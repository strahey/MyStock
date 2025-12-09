import { GoogleLogin } from '@react-oauth/google'
import { useAuth } from './AuthContext'
import './Login.css'

const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID || ''

function Login() {
  const { login } = useAuth()

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

  if (!GOOGLE_CLIENT_ID) {
    return (
      <div className="login-container">
        <div className="login-card">
          <h1>MyStock</h1>
          <p className="error-message">
            Google OAuth is not configured. Please set VITE_GOOGLE_CLIENT_ID in your environment variables.
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="login-container">
      <div className="login-card">
        <h1>MyStock</h1>
        <p className="subtitle">LEGO Inventory Management System</p>
        <p className="description">Sign in with your Google account to continue</p>
        <div className="google-login-wrapper">
          <GoogleLogin
            onSuccess={handleGoogleSuccess}
            onError={handleGoogleError}
            useOneTap={false}
          />
        </div>
      </div>
    </div>
  )
}

export default Login

