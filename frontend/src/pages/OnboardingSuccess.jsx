// OnboardingSuccess.jsx — "You're all set!" page at "/onboarding-success".
// Shown after completing onboarding for all roles (patient, doctor, admin).

import { useNavigate, useLocation, Navigate } from 'react-router-dom'
import medicalIcon from '../assets/medicalPng.png'
import '../styles/onboardingSuccess.css'

const Checkmark = () => (
  <svg
    className="success-checkmark"
    viewBox="0 0 24 24"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
  >
    <polyline
      points="4 13 9 18 20 7"
      stroke="currentColor"
      strokeWidth="2.5"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
)

function OnboardingSuccess() {
  const navigate = useNavigate()
  const { state } = useLocation()

  // Guard: must arrive here from an onboarding detail page
  if (!state?.fromOnboarding) {
    return <Navigate to="/register" replace />
  }

  return (
    <div className="success-page">
      <div className="success-card">

        <img src={medicalIcon} alt="" className="success-bg-icon" aria-hidden="true" />

        {/* Step dots — step 3 active */}
        <div className="success-step-dots">
          <div className="success-step-dot" />
          <div className="success-step-dot" />
          <div className="success-step-dot active" />
        </div>

        <div className="success-body">
          <div className="success-icon-wrap">
            <Checkmark />
          </div>

          <h1>You're all set!</h1>

          <p className="success-subtitle">
            Your account has been set up successfully. You are ready to get started with scheduling.
          </p>

  
          <button className="success-btn" onClick={() => navigate('/', { replace: true })}>
            Continue
          </button>
        </div>

      </div>
    </div>
  )
}

export default OnboardingSuccess
