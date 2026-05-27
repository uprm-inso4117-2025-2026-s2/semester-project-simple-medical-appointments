// Register.jsx — "Create an account" page at "/register".
// Matches the Figma "sign up" frame: centered white card on teal gradient.

import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { signUpOnly } from '../services/authService'
import medicalIcon from '../assets/medicalPng.png'
import '../styles/auth.css'

// Eye icons for the password visibility toggle
const EyeOpen = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
    <circle cx="12" cy="12" r="3" />
  </svg>
)

const EyeOff = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94" />
    <path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19" />
    <line x1="1" y1="1" x2="23" y2="23" />
  </svg>
)

function PasswordInput({ id, name, value, onChange, placeholder, hasError }) {
  const [visible, setVisible] = useState(false)
  return (
    <div className="input-wrap">
      <input
        id={id}
        type={visible ? 'text' : 'password'}
        name={name}
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        required
        autoComplete="new-password"
        className={hasError ? 'input-error' : ''}
      />
      <button
        type="button"
        className="eye-btn"
        onClick={() => setVisible((v) => !v)}
        aria-label={visible ? 'Hide password' : 'Show password'}
      >
        {visible ? <EyeOff /> : <EyeOpen />}
      </button>
    </div>
  )
}

function Register() {
  const navigate = useNavigate()

  const [fields, setFields] = useState({
    firstName: '',
    lastName: '',
    email: '',
    password: '',
    confirmPassword: '',
  })
  const [error, setError] = useState(null)
  const [passwordMismatch, setPasswordMismatch] = useState(false)
  const [loading, setLoading] = useState(false)
  const [success, setSuccess] = useState(false)
  const [emailConfirmationRequired, setEmailConfirmationRequired] = useState(false)

  const handleChange = (e) => {
    const { name, value } = e.target
    setFields((prev) => ({ ...prev, [name]: value }))
    setError(null)
    if (name === 'confirmPassword' || name === 'password') {
      setPasswordMismatch(false)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)
    setPasswordMismatch(false)

    if (fields.password !== fields.confirmPassword) {
      setPasswordMismatch(true)
      return
    }

    setLoading(true)
    try {
      const result = await signUpOnly(fields.email, fields.password)

      navigate('/role-selection', {
        state: {
          userId:                    result.user.id,
          firstName:                 fields.firstName,
          lastName:                  fields.lastName,
          username:                  fields.email.split('@')[0],
          emailConfirmationRequired: result.emailConfirmationRequired,
        },
      })
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  // Email confirmation screen
  if (emailConfirmationRequired) {
    return (
      <div className="auth-bg">
        <div className="auth-card auth-confirm">
          <h1>Check your email</h1>
          <p>
            We sent a confirmation link to <strong>{fields.email}</strong>.
          </p>
          <p>Click the link in the email to activate your account.</p>
          <Link to="/" style={{ display: 'inline-block', marginTop: '1.25rem', color: '#1b5e7d', fontWeight: 600 }}>
            Back to home
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="auth-bg">
      <div className="register-card">
        {/* Decorative watermark — Figma: 784×784px Mask group at x=279,y=19 in 900×900 card */}
        <img src={medicalIcon} alt="" className="register-bg-icon" aria-hidden="true" />

        <h1>Create an account</h1>
        <p className="auth-subtitle">
          Already have an account? <Link to="/login">Log in</Link>
        </p>

        <form onSubmit={handleSubmit} noValidate>
          {/* First Name + Last Name side by side */}
          <div className="form-row">
            <div className="form-group">
              <label htmlFor="firstName">First Name</label>
              <input
                id="firstName"
                type="text"
                name="firstName"
                value={fields.firstName}
                onChange={handleChange}
                required
                autoComplete="given-name"
              />
            </div>
            <div className="form-group">
              <label htmlFor="lastName">Last Name</label>
              <input
                id="lastName"
                type="text"
                name="lastName"
                value={fields.lastName}
                onChange={handleChange}
                required
                autoComplete="family-name"
              />
            </div>
          </div>

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
            <PasswordInput
              id="password"
              name="password"
              value={fields.password}
              onChange={handleChange}
              placeholder=""
              hasError={passwordMismatch}
            />
          </div>

          <div className="form-group">
            <label htmlFor="confirmPassword">Confirm Password</label>
            <PasswordInput
              id="confirmPassword"
              name="confirmPassword"
              value={fields.confirmPassword}
              onChange={handleChange}
              placeholder=""
              hasError={passwordMismatch}
            />
            {passwordMismatch && (
              <p className="field-error">Password does not match</p>
            )}
          </div>

          {error && (
            <p className="auth-error" role="alert">
              {error}
            </p>
          )}

          <button
            type="submit"
            className={`auth-btn${success ? ' success' : ''}`}
            disabled={loading || success}
          >
            {success ? 'Success!' : loading ? 'Creating account…' : 'Create Account'}
          </button>
        </form>
      </div>
    </div>
  )
}

export default Register

