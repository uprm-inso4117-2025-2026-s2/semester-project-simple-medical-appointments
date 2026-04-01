

import { useState } from 'react'
import { useNavigate, useLocation, Navigate } from 'react-router-dom'
import { syncRegistration } from '../services/api'
import medicalIcon from '../assets/medicalPng.png'
import '../styles/auth.css'
import '../styles/patientDetails.css'
import '../styles/doctorDetails.css'

// ── Phone formatter ────────────────────────────────────────────────────
function formatPhone(value) {
  const digits = value.replace(/\D/g, '').slice(0, 10)
  if (digits.length <= 3) return digits
  if (digits.length <= 6) return `(${digits.slice(0, 3)}) ${digits.slice(3)}`
  return `(${digits.slice(0, 3)}) ${digits.slice(3, 6)}-${digits.slice(6)}`
}

// ── Validation ─────────────────────────────────────────────────────────
function validate(fields) {
  const errors = {}

  if (!fields.professionTitle.trim())
    errors.professionTitle = 'Profession title is required.'

  if (!fields.specialty.trim())
    errors.specialty = 'Specialty is required.'

  if (!fields.licenseNumber.trim())
    errors.licenseNumber = 'License number is required.'

  if (!fields.licenseState.trim())
    errors.licenseState = 'License state is required.'

  const phoneDigits = fields.phoneNumber.replace(/\D/g, '')
  if (!fields.phoneNumber)
    errors.phoneNumber = 'Phone number is required.'
  else if (phoneDigits.length < 10)
    errors.phoneNumber = 'Enter a valid 10-digit phone number.'

  return errors
}

function DoctorDetails() {
  const navigate = useNavigate()
  const { state } = useLocation()

  // Guard: must arrive here from RoleSelection as a doctor
  if (!state?.userId || state?.role !== 'doctor') {
    return <Navigate to="/register" replace />
  }

  const [fields, setFields] = useState({
    professionTitle: '',
    specialty:       '',
    licenseNumber:   '',
    licenseState:    '',
    phoneNumber:     '',
    bio:             '',
  })

  const [errors, setErrors]       = useState({})
  const [loading, setLoading]     = useState(false)
  const [formError, setFormError] = useState(null)

  const handleChange = (e) => {
    const { name, value } = e.target
    setFields(prev => ({ ...prev, [name]: value }))
    if (errors[name]) setErrors(prev => ({ ...prev, [name]: null }))
  }

  const handlePhoneChange = (e) => {
    const formatted = formatPhone(e.target.value)
    setFields(prev => ({ ...prev, phoneNumber: formatted }))
    if (errors.phoneNumber) setErrors(prev => ({ ...prev, phoneNumber: null }))
  }

  const handleSubmit = async () => {
    const validationErrors = validate(fields)
    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors)
      return
    }

    setLoading(true)
    setFormError(null)

    try {
      await syncRegistration({
        user_id:          state.userId,
        first_name:       state.firstName,
        last_name:        state.lastName,
        username:         state.username,
        role:             state.role,
        phone_number:     fields.phoneNumber,
        profession_title: fields.professionTitle,
        specialty:        fields.specialty,
        license_number:   fields.licenseNumber,
        license_state:    fields.licenseState,
        bio:              fields.bio || null,
      })

      navigate('/onboarding-success', { state: { fromOnboarding: true }, replace: true })
    } catch (err) {
      setFormError('Something went wrong. Please try again.')
      console.error('Doctor details sync failed:', err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="doctor-details-page">
      <div className="doctor-details-card">

        <img src={medicalIcon} alt="" className="doctor-details-bg-icon" aria-hidden="true" />

        {/* Step dots — step 2 active */}
        <div className="doctor-step-dots">
          <div className="doctor-step-dot" />
          <div className="doctor-step-dot active" />
          <div className="doctor-step-dot" />
        </div>

        <h1>Doctor Details</h1>
        <p className="doctor-details-subtitle">Almost there. Tell us about your practice.</p>

        {/* ── Professional Information ── */}
        <p className="pd-section-label">Professional Information</p>

        <div className="pd-form-row">
          <div className="pd-field">
            <div className="pd-label-row">
              <span className="pd-label">Profession Title</span>
            </div>
            <input
              className={`pd-input${errors.professionTitle ? ' error' : ''}`}
              type="text"
              name="professionTitle"
              value={fields.professionTitle}
              onChange={handleChange}
              placeholder="e.g. Cardiologist"
            />
            {errors.professionTitle && <span className="pd-field-error">{errors.professionTitle}</span>}
          </div>

          <div className="pd-field">
            <div className="pd-label-row">
              <span className="pd-label">Specialty</span>
            </div>
            <input
              className={`pd-input${errors.specialty ? ' error' : ''}`}
              type="text"
              name="specialty"
              value={fields.specialty}
              onChange={handleChange}
              placeholder="e.g. Cardiology"
            />
            {errors.specialty && <span className="pd-field-error">{errors.specialty}</span>}
          </div>
        </div>

        <div className="pd-divider" />

        {/* ── License ── */}
        <p className="pd-section-label">License</p>

        <div className="pd-form-row">
          <div className="pd-field">
            <div className="pd-label-row">
              <span className="pd-label">License Number</span>
            </div>
            <input
              className={`pd-input${errors.licenseNumber ? ' error' : ''}`}
              type="text"
              name="licenseNumber"
              value={fields.licenseNumber}
              onChange={handleChange}
            />
            {errors.licenseNumber && <span className="pd-field-error">{errors.licenseNumber}</span>}
          </div>

          <div className="pd-field">
            <div className="pd-label-row">
              <span className="pd-label">License State</span>
            </div>
            <input
              className={`pd-input${errors.licenseState ? ' error' : ''}`}
              type="text"
              name="licenseState"
              value={fields.licenseState}
              onChange={handleChange}
              placeholder="e.g. PR"
              maxLength={2}
            />
            {errors.licenseState && <span className="pd-field-error">{errors.licenseState}</span>}
          </div>
        </div>

        <div className="pd-divider" />

        {/* ── Contact ── */}
        <p className="pd-section-label">Contact</p>

        <div className="pd-form-half">
          <div className="pd-field">
            <div className="pd-label-row">
              <span className="pd-label">Phone Number</span>
            </div>
            <input
              className={`pd-input${errors.phoneNumber ? ' error' : ''}`}
              type="tel"
              name="phoneNumber"
              value={fields.phoneNumber}
              onChange={handlePhoneChange}
              placeholder="+1 (787) 000-0000"
              maxLength={14}
            />
            {errors.phoneNumber && <span className="pd-field-error">{errors.phoneNumber}</span>}
          </div>
        </div>

        <div className="pd-divider" />

        {/* ── About ── */}
        <p className="pd-section-label">About</p>

        <div className="pd-field">
          <div className="pd-label-row">
            <span className="pd-label">Bio</span>
            <span className="pd-optional">(optional)</span>
          </div>
          <textarea
            className="pd-textarea"
            name="bio"
            value={fields.bio}
            onChange={handleChange}
            placeholder=""
          />
        </div>

        {formError && <p className="auth-error" role="alert">{formError}</p>}

        <button
          className="auth-btn"
          onClick={handleSubmit}
          disabled={loading}
        >
          {loading ? 'Saving…' : 'Complete Setup'}
        </button>

      </div>
    </div>
  )
}

export default DoctorDetails
