// Login.jsx — "Log in" page at "/login".
// Matches the Figma "log in" frame. Auth logic is a stub for the Login issue.

import { useState } from 'react'
import { Link } from 'react-router-dom'
import medicalIcon from '../assets/medicalPng.png'
import eyeOffIcon from '../assets/bef1c8a9a00da60f9252fd4a814e014de9962e13.png'
import '../styles/auth.css'

const EyeOpen = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
    <circle cx="12" cy="12" r="3" />
  </svg>
)

function Login() {
  const [fields, setFields] = useState({ email: '', password: '' })
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)

  const handleChange = (e) => {
    setFields((prev) => ({ ...prev, [e.target.name]: e.target.value }))
    setError(null)
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      // TODO: implement supabase.auth.signInWithPassword in the Login auth-flow issue
      throw new Error('Login not yet implemented.')
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="login-page">
      <div className="login-card">

        {/* Left — branding panel */}
        <div className="login-left">
          <img
            src={medicalIcon}
            alt=""
            className="login-left-icon"
            style={{ filter: 'brightness(0) invert(1)' }}
          />
          <h2>Welcome Back!</h2>
          <p>Healthcare scheduling made simple.</p>
        </div>

        {/* Right — form panel */}
        <div className="login-right">
          <h1>Log in</h1>
          <p className="auth-subtitle">
            Don't have an account? <Link to="/register">Create an account</Link>
          </p>

          <form onSubmit={handleSubmit} noValidate>
            <div className="form-group">
              <label htmlFor="email">Email Address</label>
              <input
                id="email"
                type="email"
                name="email"
                value={fields.email}
                onChange={handleChange}
                required
                autoComplete="email"
              />
            </div>

            <div className="form-group">
              <label htmlFor="password">Password</label>
              <div className="input-wrap">
                <input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  name="password"
                  value={fields.password}
                  onChange={handleChange}
                  required
                  autoComplete="current-password"
                />
                <button
                  type="button"
                  className="eye-btn"
                  onClick={() => setShowPassword((v) => !v)}
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword
                    ? <EyeOpen />
                    : <img src={eyeOffIcon} alt="Hide" width="20" height="20" style={{ opacity: 0.45 }} />
                  }
                </button>
              </div>
              <Link to="/forgot-password" className="forgot-link">
                Forgot password?
              </Link>
            </div>

            {error && (
              <p className="auth-error" role="alert">{error}</p>
            )}

            <button type="submit" className="auth-btn" disabled={loading}>
              {loading ? 'Logging in…' : 'Log in'}
            </button>
          </form>
        </div>

      </div>
    </div>
  )
}

export default Login
