// AdminDetails.jsx — "Admin Access" onboarding step at "/admin-details".
// Only reachable from RoleSelection when role === 'admin'.
// TODO: access code verification against backend not yet implemented.
// Currently syncs user to DB and navigates to admin dashboard without verifying the code.

import { useState } from 'react'
import { useNavigate, useLocation, Navigate } from 'react-router-dom'
import { syncRegistration } from '../services/api'
import '../styles/auth.css'
import '../styles/adminDetails.css'

const InfoIcon = () => (
  <svg className="admin-info-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="1.8" />
    <line x1="12" y1="11" x2="12" y2="17" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
    <circle cx="12" cy="7.5" r="0.75" fill="currentColor" stroke="currentColor" strokeWidth="0.5" />
  </svg>
)

function AdminDetails() {
  const navigate = useNavigate()
  const { state } = useLocation()

  // Guard: must arrive here from RoleSelection as an admin
  if (!state?.userId || state?.role !== 'admin') {
    return <Navigate to="/register" replace />
  }

  const [accessCode, setAccessCode]   = useState('')
  const [error, setError]             = useState(null)
  const [loading, setLoading]         = useState(false)
  const [formError, setFormError]     = useState(null)

  const handleChange = (e) => {
    setAccessCode(e.target.value.toUpperCase())
    if (error) setError(null)
  }

  const handleSubmit = async () => {
    if (!accessCode.trim()) {
      setError('Please enter the clinic access code.')
      return
    }

    setLoading(true)
    setFormError(null)

    try {
      // TODO: verify accessCode against backend before syncing
      await syncRegistration({
        user_id:    state.userId,
        first_name: state.firstName,
        last_name:  state.lastName,
        username:   state.username,
        role:       state.role,
      })

      navigate('/onboarding-success', { state: { fromOnboarding: true }, replace: true })
    } catch (err) {
      setFormError('Something went wrong. Please try again.')
      console.error('Admin sync failed:', err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="admin-details-page">
      <div className="admin-details-card">

        {/* Step dots — step 2 active */}
        <div className="admin-step-dots">
          <div className="admin-step-dot" />
          <div className="admin-step-dot active" />
          <div className="admin-step-dot" />
        </div>

        <h1>Admin Access</h1>
        <p className="admin-details-subtitle">
          Enter the clinic access code provided by your system administrator.
        </p>

        <p className="admin-field-label">Clinic Access Code</p>

        <input
          className={`admin-code-input${error ? ' error' : ''}`}
          type="text"
          value={accessCode}
          onChange={handleChange}
          placeholder="e.g. CLINIC-XXXX-XXXX"
          autoComplete="off"
          spellCheck={false}
        />
        {error && <span className="admin-field-error">{error}</span>}

        <div className="admin-info-box">
          <InfoIcon />
          <p className="admin-info-text">
            Your access code is provided by your clinic administrator. If you do not have one, contact{' '}
            <strong>your clinic directly</strong> to request access.
          </p>
        </div>

        {formError && <p className="auth-error" role="alert">{formError}</p>}

        <button
          className="auth-btn"
          onClick={handleSubmit}
          disabled={loading}
        >
          {loading ? 'Saving…' : 'Verify & Continue'}
        </button>

      </div>
    </div>
  )
}

export default AdminDetails
