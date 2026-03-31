// DoctorProfile.jsx — Doctor profile page at "/doctor-profile".
// All data fetched from GET /api/profile/:userId which returns fields from:
//   profiles, providers, provider_settings, profile_settings tables.

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

function formatMinutes(value) {
  if (value == null) return '—'
  return `${value} minutes`
}

function getInitials(firstName, lastName) {
  const f = firstName?.[0] ?? ''
  const l = lastName?.[0] ?? ''
  return (f + l).toUpperCase() || '?'
}

// ── Reusable field ────────────────────────────────────────────────────────────
function InfoField({ label, value, wide }) {
  return (
    <div className={`dp-field${wide ? ' dp-field--wide' : ''}`}>
      <p className="dp-field-label">{label}</p>
      <p className="dp-field-value">{value || '—'}</p>
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

function DoctorProfile() {
  const navigate = useNavigate()
  const [profile, setProfile]       = useState(null)
  const [userId, setUserId]         = useState(null)
  const [authorized, setAuthorized] = useState(
    () => sessionStorage.getItem('userRole') === 'doctor'
  )

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
    // Optimistic update
    setProfile(prev => ({ ...prev, [field]: next }))
    try {
      await updateProfile(userId, { [field]: next })
    } catch {
      // Revert on failure
      setProfile(prev => ({ ...prev, [field]: current }))
    }
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
          {/* TODO: wire up once edit profile flow is built */}
          <button className="dp-edit-btn" onClick={() => {}}>Edit Profile</button>
        </div>

        {/* ── Personal Information ── */}
        <p className="dp-section-label">PERSONAL INFORMATION</p>
        <div className="dp-divider" />
        <div className="dp-fields-grid">
          <InfoField label="FIRST NAME"   value={profile?.first_name} />
          <InfoField label="LAST NAME"    value={profile?.last_name} />
          <InfoField label="PHONE NUMBER" value={profile?.phone_number} />
        </div>

        {/* ── Professional Information ── */}
        <p className="dp-section-label">PROFESSIONAL INFORMATION</p>
        <div className="dp-divider" />
        <div className="dp-fields-grid">
          <InfoField label="PROFESSION TITLE" value={profile?.profession_title} />
          <InfoField label="SPECIALTY"        value={profile?.specialty} />
          <InfoField label="LICENSE NUMBER"   value={profile?.license_number} />
          <InfoField label="LICENSE STATE"    value={profile?.license_state} />
          <InfoField label="BIO"              value={profile?.bio} wide />
        </div>

        {/* ── Appointment Settings ── */}
        <p className="dp-section-label">APPOINTMENT SETTINGS</p>
        <div className="dp-divider" />
        <div className="dp-fields-grid">
          <InfoField label="APPOINTMENT BUFFER" value={formatMinutes(profile?.appointment_buffer_minutes)} />
          <InfoField label="DEFAULT DURATION"   value={formatMinutes(profile?.default_appointment_duration)} />
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
