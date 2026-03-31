// PatientDetails.jsx — "Patient Details" onboarding step at "/patient-details".
// Only reachable from RoleSelection when role === 'patient'.
// DB sync is handled here for testing; will move to final onboarding step once all steps are built.

import { useState } from 'react'
import { useNavigate, useLocation, Navigate } from 'react-router-dom'
import { syncRegistration } from '../services/api'
import medicalIcon from '../assets/medicalPng.png'
import '../styles/auth.css'
import '../styles/patientDetails.css'




// ── Phone formatter ────────────────────────────────────────────────────
// Formats raw digits as (787) 000-0000 (10 digit max)
function formatPhone(value) {
  const digits = value.replace(/\D/g, '').slice(0, 10)
  if (digits.length <= 3) return digits
  if (digits.length <= 6) return `(${digits.slice(0, 3)}) ${digits.slice(3)}`
  return `(${digits.slice(0, 3)}) ${digits.slice(3, 6)}-${digits.slice(6)}`
}

// ── Validation ─────────────────────────────────────────────────────────
function validate(fields) {
  const errors = {}
  const today = new Date().toISOString().split('T')[0]

  if (!fields.dateOfBirth) {
    errors.dateOfBirth = 'Date of birth is required.'
  } else if (fields.dateOfBirth > today) {
    errors.dateOfBirth = 'Date of birth cannot be in the future.'
  }

  const phoneDigits = fields.phoneNumber.replace(/\D/g, '')
  if (!fields.phoneNumber) {
    errors.phoneNumber = 'Phone number is required.'
  } else if (phoneDigits.length < 10) {
    errors.phoneNumber = 'Enter a valid 10-digit phone number.'
  }

  if (!fields.gender) {
    errors.gender = 'Please select a gender.'
  }

  if (!fields.emergencyContactName.trim()) {
    errors.emergencyContactName = 'Contact name is required.'
  }

  const contactDigits = fields.emergencyContactPhone.replace(/\D/g, '')
  if (!fields.emergencyContactPhone) {
    errors.emergencyContactPhone = 'Contact phone is required.'
  } else if (contactDigits.length < 10) {
    errors.emergencyContactPhone = 'Enter a valid 10-digit phone number.'
  }

  return errors
}

function PatientDetails() {
  const navigate = useNavigate()
  const { state } = useLocation()

  // Guard: must arrive here from RoleSelection as a patient
  if (!state?.userId || state?.role !== 'patient') {
    return <Navigate to="/register" replace />
  }

  const [fields, setFields] = useState({
    dateOfBirth:            '',
    phoneNumber:            '',
    gender:                 '',
    insuranceProvider:      '',
    insuranceMemberId:      '',
    emergencyContactName:   '',
    emergencyContactPhone:  '',
  })

  const [errors, setErrors]   = useState({})
  const [loading, setLoading] = useState(false)
  const [formError, setFormError] = useState(null)

  const handleChange = (e) => {
    const { name, value } = e.target
    setFields(prev => ({ ...prev, [name]: value }))
    if (errors[name]) setErrors(prev => ({ ...prev, [name]: null }))
  }

  const handlePhoneChange = (name) => (e) => {
    const formatted = formatPhone(e.target.value)
    setFields(prev => ({ ...prev, [name]: formatted }))
    if (errors[name]) setErrors(prev => ({ ...prev, [name]: null }))
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
        user_id:                      state.userId,
        first_name:                   state.firstName,
        last_name:                    state.lastName,
        username:                     state.username,
        role:                         state.role,
        phone_number:                 fields.phoneNumber,
        date_of_birth:                fields.dateOfBirth,
        gender:                       fields.gender,
        insurance_provider:           fields.insuranceProvider   || null,
        insurance_member_id:          fields.insuranceMemberId   || null,
        emergency_contact_name:       fields.emergencyContactName,
        emergency_contact_phone:      fields.emergencyContactPhone,
      })

      // TODO: replace '/' with next onboarding step once added
      navigate('/', { replace: true })
    } catch (err) {
      setFormError('Something went wrong. Please try again.')
      console.error('Patient details sync failed:', err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="patient-details-page">
      <div className="patient-details-card">

        <img src={medicalIcon} alt="" className="patient-details-bg-icon" aria-hidden="true" />

        {/* Step dots — step 2 active */}
        <div className="patient-step-dots">
          <div className="patient-step-dot" />
          <div className="patient-step-dot active" />
          <div className="patient-step-dot" />
        </div>

        <h1>Patient Details</h1>
        <p className="patient-details-subtitle">Almost there. Tell us a bit more about yourself.</p>

        {/* ── Personal Information ── */}
        <p className="pd-section-label">Personal Information</p>

        <div className="pd-form-row">
          {/* Date of Birth */}
          <div className="pd-field">
            <div className="pd-label-row">
              <span className="pd-label">Date of Birth</span>
            </div>
            <input
              className={`pd-input${errors.dateOfBirth ? ' error' : ''}`}
              type="date"
              name="dateOfBirth"
              value={fields.dateOfBirth}
              onChange={handleChange}
              max={new Date().toISOString().split('T')[0]}
            />
            {errors.dateOfBirth && <span className="pd-field-error">{errors.dateOfBirth}</span>}
          </div>

          {/* Phone Number */}
          <div className="pd-field">
            <div className="pd-label-row">
              <span className="pd-label">Phone Number</span>
            </div>
            <input
              className={`pd-input${errors.phoneNumber ? ' error' : ''}`}
              type="tel"
              name="phoneNumber"
              value={fields.phoneNumber}
              onChange={handlePhoneChange('phoneNumber')}
              placeholder="+1 (787) 000-0000"
              maxLength={14}
            />
            {errors.phoneNumber && <span className="pd-field-error">{errors.phoneNumber}</span>}
          </div>
        </div>

        {/* Gender — left column only */}
        <div className="pd-form-half">
          <div className="pd-field">
            <div className="pd-label-row">
              <span className="pd-label">Gender</span>
            </div>
            <select
              className={`pd-select${!fields.gender ? ' placeholder' : ''}${errors.gender ? ' error' : ''}`}
              name="gender"
              value={fields.gender}
              onChange={handleChange}
            >
              <option value="" disabled>Select Gender</option>
              <option value="male">Male</option>
              <option value="female">Female</option>
              <option value="non-binary">Non-binary</option>
              <option value="prefer_not_to_say">Prefer not to say</option>
            </select>
            {errors.gender && <span className="pd-field-error">{errors.gender}</span>}
          </div>
        </div>

        <div className="pd-divider" />

        {/* ── Insurance ── */}
        <p className="pd-section-label">Insurance</p>

        <div className="pd-form-row">
          {/* Insurance Provider */}
          <div className="pd-field">
            <div className="pd-label-row">
              <span className="pd-label">Insurance Provider</span>
              <span className="pd-optional">(optional)</span>
            </div>
            <input
              className="pd-input"
              type="text"
              name="insuranceProvider"
              value={fields.insuranceProvider}
              onChange={handleChange}
            />
          </div>

          {/* Member ID */}
          <div className="pd-field">
            <div className="pd-label-row">
              <span className="pd-label">Member ID</span>
              <span className="pd-optional">(optional)</span>
            </div>
            <input
              className="pd-input"
              type="text"
              name="insuranceMemberId"
              value={fields.insuranceMemberId}
              onChange={handleChange}
            />
          </div>
        </div>

        <div className="pd-divider" />

        {/* ── Emergency Contact ── */}
        <p className="pd-section-label">Emergency Contact</p>

        <div className="pd-form-row">
          {/* Contact Name */}
          <div className="pd-field">
            <div className="pd-label-row">
              <span className="pd-label">Contact Name</span>
            </div>
            <input
              className={`pd-input${errors.emergencyContactName ? ' error' : ''}`}
              type="text"
              name="emergencyContactName"
              value={fields.emergencyContactName}
              onChange={handleChange}
            />
            {errors.emergencyContactName && <span className="pd-field-error">{errors.emergencyContactName}</span>}
          </div>

          {/* Contact Phone */}
          <div className="pd-field">
            <div className="pd-label-row">
              <span className="pd-label">Contact Phone</span>
            </div>
            <input
              className={`pd-input${errors.emergencyContactPhone ? ' error' : ''}`}
              type="tel"
              name="emergencyContactPhone"
              value={fields.emergencyContactPhone}
              onChange={handlePhoneChange('emergencyContactPhone')}
              placeholder="+1 (787) 000-0000"
              maxLength={14}
            />
            {errors.emergencyContactPhone && <span className="pd-field-error">{errors.emergencyContactPhone}</span>}
          </div>
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

export default PatientDetails
