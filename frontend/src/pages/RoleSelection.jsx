import { useState } from 'react'
import { useNavigate, useLocation, Navigate } from 'react-router-dom'
import { syncRegistration } from '../services/api'
import '../styles/auth.css'
import '../styles/roleSelection.css'

const PatientIcon = () => (
  <svg className="role-card-icon" width="56" height="68" viewBox="0 0 56 68" fill="none" xmlns="http://www.w3.org/2000/svg">
    <circle cx="28" cy="19" r="15" stroke="#113C51" strokeWidth="2.5" />
    <path d="M4 62c0-13.255 10.745-24 24-24s24 10.745 24 24" stroke="#113C51" strokeWidth="2.5" strokeLinecap="round" />
  </svg>
)

const DoctorIcon = () => (
  <svg className="role-card-icon" width="56" height="68" viewBox="0 0 56 68" fill="none" xmlns="http://www.w3.org/2000/svg">
    <circle cx="22" cy="18" r="14" stroke="#113C51" strokeWidth="2.5" />
    <path d="M2 58c0-12.15 8.954-22 20-22" stroke="#113C51" strokeWidth="2.5" strokeLinecap="round" />
    <circle cx="42" cy="50" r="12" stroke="#113C51" strokeWidth="2.5" />
    <line x1="42" y1="44" x2="42" y2="56" stroke="#113C51" strokeWidth="2.5" strokeLinecap="round" />
    <line x1="36" y1="50" x2="48" y2="50" stroke="#113C51" strokeWidth="2.5" strokeLinecap="round" />
  </svg>
)

const AdminIcon = () => (
  <svg className="role-card-icon" width="56" height="56" viewBox="0 0 56 56" fill="none" xmlns="http://www.w3.org/2000/svg">
    <rect x="4" y="10" width="48" height="42" rx="6" stroke="#113C51" strokeWidth="2.5" />
    <line x1="4" y1="24" x2="52" y2="24" stroke="#113C51" strokeWidth="2.5" />
    <line x1="17" y1="4" x2="17" y2="18" stroke="#113C51" strokeWidth="2.5" strokeLinecap="round" />
    <line x1="39" y1="4" x2="39" y2="18" stroke="#113C51" strokeWidth="2.5" strokeLinecap="round" />
    <line x1="14" y1="34" x2="42" y2="34" stroke="#113C51" strokeWidth="2" strokeLinecap="round" />
    <line x1="14" y1="44" x2="34" y2="44" stroke="#113C51" strokeWidth="2" strokeLinecap="round" />
  </svg>
)

const ROLES = [
  {
    id: 'patient',
    label: 'Patient',
    description: 'Book appointments, view your medical history and manage your health.',
    icon: PatientIcon,
  },
  {
    id: 'doctor',
    label: 'Doctor',
    description: 'Manage your schedule, view patient records and handle appointments.',
    icon: DoctorIcon,
  },
  {
    id: 'admin',
    label: 'Admin',
    description: 'Oversee clinic operations, manage staff and configure the system.',
    icon: AdminIcon,
  },
]

function RoleSelection() {
  const navigate = useNavigate()
  const { state } = useLocation()
  const [selected, setSelected] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  // Guard: must arrive here from registration flow
  if (!state?.userId) {
    return <Navigate to="/register" replace />
  }

  const handleContinue = async () => {
    if (!selected) {
      setError('Please select a role to continue.')
      return
    }

    const nextState = { ...state, role: selected }

    // Patient — defer sync to PatientDetails
    if (selected === 'patient') {
      navigate('/patient-details', { state: nextState })
      return
    }

    // Doctor — defer sync to DoctorDetails
    if (selected === 'doctor') {
      navigate('/doctor-details', { state: nextState })
      return
    }

    // Admin: no details page yet — sync now for testing
    setLoading(true)
    setError(null)

    try {
      await syncRegistration({
        user_id:    state.userId,
        first_name: state.firstName,
        last_name:  state.lastName,
        username:   state.username,
        role:       selected,
      })

      // TODO: replace '/' with admin detail route once added
      navigate('/', { replace: true })
    } catch (err) {
      setError('Something went wrong saving your role. Please try again.')
      console.error('Role sync failed:', err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="role-selection-page">
      <div className="role-selection-card">

        <div className="role-step-dots">
          <div className="role-step-dot active" />
          <div className="role-step-dot" />
          <div className="role-step-dot" />
        </div>

        <h1>I am a...</h1>
        <p className="role-selection-subtitle">Select your role to continue setting up your account.</p>

        <div className="role-cards-grid">
          {ROLES.map(({ id, label, description, icon: Icon }) => (
            <div
              key={id}
              className={`role-card${selected === id ? ' selected' : ''}`}
              onClick={() => { setSelected(id); setError(null) }}
              role="button"
              tabIndex={0}
              aria-pressed={selected === id}
              onKeyDown={(e) => e.key === 'Enter' && setSelected(id)}
            >
              <Icon />
              <h3>{label}</h3>
              <p>{description}</p>
            </div>
          ))}
        </div>

        {error && <p className="auth-error" role="alert">{error}</p>}

        <button
          className="auth-btn"
          onClick={handleContinue}
          disabled={!selected || loading}
        >
          {loading ? 'Saving…' : 'Continue'}
        </button>

      </div>
    </div>
  )
}

export default RoleSelection
