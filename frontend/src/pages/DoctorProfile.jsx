

import { useEffect, useState } from 'react'
import { useNavigate, Navigate } from 'react-router-dom'
import { supabase } from '../lib/supabaseClient'
import { getProfile, updateProfile } from '../services/api'

import calendarIcon  from '../assets/calendar_icon.svg'
import documentsIcon from '../assets/documents_icon.svg'
import settingsIcon  from '../assets/settings_icon.svg'
import logoutIcon    from '../assets/logout_icon.svg'

import '../styles/doctorProfile.css'

// ── Inline icons ──────────────────────────────────────────────────────────────
const IconDashboard = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <rect x="3" y="3" width="7" height="7" rx="1"/>
    <rect x="14" y="3" width="7" height="7" rx="1"/>
    <rect x="3" y="14" width="7" height="7" rx="1"/>
    <rect x="14" y="14" width="7" height="7" rx="1"/>
  </svg>
)
const IconBack = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="15 18 9 12 15 6"/>
  </svg>
)
const IconUser = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
    <circle cx="12" cy="7" r="4"/>
  </svg>
)

function formatPhone(value) {
  const digits = value.replace(/\D/g, '').slice(0, 10)
  if (digits.length <= 3) return digits
  if (digits.length <= 6) return `(${digits.slice(0, 3)}) ${digits.slice(3)}`
  return `(${digits.slice(0, 3)}) ${digits.slice(3, 6)}-${digits.slice(6)}`
}

function formatMinutes(value) {
  if (value == null) return '—'
  return `${value} minutes`
}

function getInitials(firstName, lastName) {
  const f = firstName?.[0] ?? ''
  const l = lastName?.[0] ?? ''
  return (f + l).toUpperCase() || '?'
}

// ── Read-only field ───────────────────────────────────────────────────────────
function InfoField({ label, value, wide }) {
  return (
    <div className={`dp-field${wide ? ' dp-field--wide' : ''}`}>
      <p className="dp-field-label">{label}</p>
      <p className="dp-field-value">{value || '—'}</p>
    </div>
  )
}

// ── Editable field ────────────────────────────────────────────────────────────
function EditField({ label, fieldKey, editValues, onChange, wide, multiline, maxLength }) {
  return (
    <div className={`dp-field dp-field--editing${wide ? ' dp-field--wide' : ''}`}>
      <p className="dp-field-label">{label}</p>
      {multiline
        ? <textarea
            className="dp-field-input dp-field-textarea"
            value={editValues[fieldKey] ?? ''}
            onChange={e => onChange(fieldKey, e.target.value)}
            rows={3}
            maxLength={maxLength}
          />
        : <input
            className="dp-field-input"
            value={editValues[fieldKey] ?? ''}
            onChange={e => onChange(fieldKey, e.target.value)}
            maxLength={maxLength}
          />
      }
    </div>
  )
}

// ── Toggle row ────────────────────────────────────────────────────────────────
function ToggleRow({ label, enabled, onChange }) {
  return (
    <div className="dp-toggle-row">
      <p className="dp-toggle-label">{label}</p>
      <button
        className={`dp-toggle ${enabled ? 'on' : 'off'}`}
        onClick={onChange}
        aria-pressed={!!enabled}
      >
        <div className="dp-toggle-knob" />
      </button>
    </div>
  )
}

// ── Editable fields for doctor ────────────────────────────────────────────────
const DOCTOR_EDIT_FIELDS = ['phone_number', 'specialty', 'bio']

function DoctorProfile() {
  const navigate = useNavigate()
  const [profile, setProfile]       = useState(null)
  const [userId, setUserId]         = useState(null)
  const [authorized, setAuthorized] = useState(
    () => sessionStorage.getItem('userRole') === 'doctor'
  )
  const [isEditing, setIsEditing]   = useState(false)
  const [editValues, setEditValues] = useState({})
  const [saveError, setSaveError]   = useState(null)
  const [saving, setSaving]         = useState(false)

  useEffect(() => {
    const checkAccess = async () => {
      const { data: { session } } = await supabase.auth.getSession()
      if (!session) {
        sessionStorage.removeItem('userRole')
        navigate('/login', { replace: true })
        return
      }

      setUserId(session.user.id)

      if (sessionStorage.getItem('userRole') === 'doctor') {
        setAuthorized(true)
        try {
          const prof = await getProfile(session.user.id)
          setProfile(prof)
        } catch {}
        return
      }

      const { data: roleRows } = await supabase
        .from('user_roles')
        .select('roles(name)')
        .eq('user_id', session.user.id)

      const role = roleRows?.[0]?.roles?.name
      if (role !== 'doctor') {
        sessionStorage.removeItem('userRole')
        navigate('/', { replace: true })
        return
      }

      sessionStorage.setItem('userRole', 'doctor')
      setAuthorized(true)

      try {
        const prof = await getProfile(session.user.id)
        setProfile(prof)
      } catch {}
    }

    checkAccess()
  }, [navigate])

  const handleLogout = async () => {
    sessionStorage.removeItem('userRole')
    await supabase.auth.signOut()
    navigate('/login')
  }

  const handleToggle = async (field) => {
    const current = profile?.[field]
    const next = !current
    setProfile(prev => ({ ...prev, [field]: next }))
    try {
      await updateProfile(userId, { [field]: next })
    } catch {
      setProfile(prev => ({ ...prev, [field]: current }))
    }
  }

  const handleEditStart = () => {
    setSaveError(null)
    setEditValues({
      phone_number: profile?.phone_number ?? '',
      specialty:    profile?.specialty    ?? '',
      bio:          profile?.bio          ?? '',
    })
    setIsEditing(true)
  }

  const handleEditCancel = () => {
    setIsEditing(false)
    setEditValues({})
    setSaveError(null)
  }

  const handleEditSave = async () => {
    // Only send fields that actually changed
    const payload = {}
    for (const field of DOCTOR_EDIT_FIELDS) {
      const edited   = editValues[field]?.trim() ?? ''
      const original = profile?.[field] ?? ''
      if (edited !== original) {
        payload[field] = edited || null
      }
    }

    if (Object.keys(payload).length === 0) {
      setIsEditing(false)
      return
    }

    // Validate phone number format before sending
    if (payload.phone_number) {
      const digits = payload.phone_number.replace(/\D/g, '')
      if (digits.length < 10) {
        setSaveError('Phone number must be a valid 10-digit number.')
        return
      }
    }

    setSaving(true)
    setSaveError(null)
    try {
      const updated = await updateProfile(userId, payload)
      setProfile(updated)
      setIsEditing(false)
      setEditValues({})
    } catch {
      setSaveError('Failed to save changes. Please try again.')
    } finally {
      setSaving(false)
    }
  }

  const handleChange = (key, value) => setEditValues(prev => ({ ...prev, [key]: value }))

  const handlePhoneChange = (key, value) => {
    setEditValues(prev => ({ ...prev, [key]: formatPhone(value) }))
  }

  if (!authorized) {
    const cached = sessionStorage.getItem('userRole')
    return <Navigate to={cached ? '/' : '/login'} replace />
  }

  const displayName = profile?.display_name ?? profile?.name ?? '…'
  const initials    = getInitials(profile?.first_name, profile?.last_name)
  const username    = profile?.username ? `@${profile.username}` : '—'
  const specialty   = profile?.specialty ?? null

  return (
    <div className="dp-layout">

      {/* ── Sidebar ── */}
      <aside className="dp-sidebar">

        <div className="dp-profile">
          <div className="dp-avatar">
            <IconUser />
          </div>
          <button className="dp-profile-name dp-profile-name--active" onClick={() => {}}>
            {displayName}
          </button>
          <span className="dp-profile-role">{specialty || 'Doctor'}</span>
        </div>

        <nav className="dp-nav">
          <div className="dp-nav-item" onClick={() => navigate('/doctor-dashboard')}>
            <span className="dp-nav-icon-svg"><IconDashboard /></span>
            <span className="dp-nav-label">Dashboard</span>
          </div>
          <div className="dp-nav-item">
            <img className="dp-nav-icon" src={calendarIcon} alt="" />
            <span className="dp-nav-label">My Appointments</span>
          </div>
          <div className="dp-nav-item">
            <img className="dp-nav-icon" src={documentsIcon} alt="" />
            <span className="dp-nav-label">Medical Records</span>
          </div>
          <div className="dp-nav-item">
            <img className="dp-nav-icon" src={settingsIcon} alt="" />
            <span className="dp-nav-label">Settings</span>
          </div>
          <div className="dp-nav-item dp-nav-logout" onClick={handleLogout}>
            <img className="dp-nav-icon" src={logoutIcon} alt="" />
            <span className="dp-nav-label">Log Out</span>
          </div>
        </nav>

      </aside>

      {/* ── Main content ── */}
      <main className="dp-main">

        <button className="dp-back-btn" onClick={() => navigate('/doctor-dashboard')}>
          <IconBack /> Dashboard
        </button>

        <h1 className="dp-heading">My Profile</h1>
        <p className="dp-subtitle">Manage your professional profile and preferences.</p>

        {/* ── Profile header card ── */}
        <div className="dp-header-card">
          <div className="dp-header-initials">{initials}</div>
          <div className="dp-header-info">
            <p className="dp-header-name">{displayName}</p>
            <p className="dp-header-username">{username}</p>
            <div className="dp-header-badges">
              <span className="dp-header-badge">Doctor</span>
              {specialty && <span className="dp-header-specialty">{specialty}</span>}
            </div>
          </div>
          {!isEditing && (
            <button className="dp-edit-btn" onClick={handleEditStart}>Edit Profile</button>
          )}
          {isEditing && (
            <div className="dp-edit-actions">
              <button className="dp-save-btn" onClick={handleEditSave} disabled={saving}>
                {saving ? 'Saving…' : 'Save Changes'}
              </button>
              <button className="dp-cancel-btn" onClick={handleEditCancel} disabled={saving}>
                Cancel
              </button>
            </div>
          )}
        </div>

        {saveError && <p className="dp-save-error">{saveError}</p>}

        {/* ── Personal Information ── */}
        <p className="dp-section-label">PERSONAL INFORMATION</p>
        <div className="dp-divider" />
        <div className="dp-fields-grid">
          <InfoField label="FIRST NAME" value={profile?.first_name} />
          <InfoField label="LAST NAME"  value={profile?.last_name} />
          {isEditing
            ? <EditField label="PHONE NUMBER" fieldKey="phone_number" editValues={editValues} onChange={handlePhoneChange} maxLength={30} />
            : <InfoField label="PHONE NUMBER" value={profile?.phone_number ? formatPhone(profile.phone_number) : null} />
          }
        </div>

        {/* ── Professional Information ── */}
        <p className="dp-section-label">PROFESSIONAL INFORMATION</p>
        <div className="dp-divider" />
        <div className="dp-fields-grid">
          <InfoField label="PROFESSION TITLE" value={profile?.profession_title} />
          {isEditing
            ? <EditField label="SPECIALTY" fieldKey="specialty" editValues={editValues} onChange={handleChange} maxLength={100} />
            : <InfoField label="SPECIALTY" value={profile?.specialty} />
          }
          <InfoField label="LICENSE NUMBER" value={profile?.license_number} />
          <InfoField label="LICENSE STATE"  value={profile?.license_state} />
          {isEditing
            ? <EditField label="BIO" fieldKey="bio" editValues={editValues} onChange={handleChange} wide multiline maxLength={1000} />
            : <InfoField label="BIO" value={profile?.bio} wide />
          }
        </div>

        {/* ── Appointment Settings ── */}
        <p className="dp-section-label">APPOINTMENT SETTINGS</p>
        <div className="dp-divider" />
        <div className="dp-fields-grid">
          <InfoField label="APPOINTMENT BUFFER"       value={formatMinutes(profile?.appointment_buffer_minutes)} />
          <InfoField label="DEFAULT DURATION"         value={formatMinutes(profile?.default_appointment_duration)} />
          {/* TODO: max_appointments_per_day is not yet in provider_settings schema */}
          <InfoField label="MAX APPOINTMENTS PER DAY" value={null} />
        </div>

        {/* ── Notifications ── */}
        <p className="dp-section-label">NOTIFICATIONS</p>
        <div className="dp-divider" />
        <div className="dp-toggles-grid">
          <ToggleRow label="Appointment Reminders" enabled={profile?.notify_appointment_reminders} onChange={() => handleToggle('notify_appointment_reminders')} />
          <ToggleRow label="Appointment Updates"   enabled={profile?.notify_appointment_updates}   onChange={() => handleToggle('notify_appointment_updates')} />
          <ToggleRow label="Messages"              enabled={profile?.notify_messages}              onChange={() => handleToggle('notify_messages')} />
        </div>

        {/* ── Preferences ── */}
        <p className="dp-section-label">PREFERENCES</p>
        <div className="dp-divider" />
        <div className="dp-fields-grid">
          <InfoField label="PREFERRED CONTACT METHOD" value={profile?.preferred_contact_method} />
          <InfoField label="PREFERRED LANGUAGE"       value={profile?.preferred_language} />
          <InfoField label="ACCESSIBILITY MODE"       value={profile?.accessibility_mode} />
        </div>

      </main>
    </div>
  )
}

export default DoctorProfile
