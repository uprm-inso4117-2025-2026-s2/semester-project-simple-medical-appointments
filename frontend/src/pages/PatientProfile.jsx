// PatientProfile.jsx — Patient profile page at "/patient-profile".
// All data fetched from GET /api/profile/:userId which returns fields from:
//   profiles, patients, profile_settings tables.
// Edit Profile button is a placeholder — wired up when edit flow is built.

import { useEffect, useState } from 'react'
import { useNavigate, Navigate } from 'react-router-dom'
import { supabase } from '../lib/supabaseClient'
import { getProfile, updateProfile } from '../services/api'

import calendarIcon  from '../assets/calendar_icon.svg'
import documentsIcon from '../assets/documents_icon.svg'
import settingsIcon  from '../assets/settings_icon.svg'
import logoutIcon    from '../assets/logout_icon.svg'

import '../styles/patientProfile.css'

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

function formatDob(dateStr) {
  if (!dateStr) return '—'
  const d = new Date(dateStr)
  return d.toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })
}

function formatMemberSince(isoStr) {
  if (!isoStr) return '—'
  const d = new Date(isoStr)
  return d.toLocaleDateString('en-US', { month: 'long', year: 'numeric' })
}

function getInitials(firstName, lastName) {
  const f = firstName?.[0] ?? ''
  const l = lastName?.[0] ?? ''
  return (f + l).toUpperCase() || '?'
}

// ── Reusable field ────────────────────────────────────────────────────────────
function InfoField({ label, value }) {
  return (
    <div className="pp-field">
      <p className="pp-field-label">{label}</p>
      <p className="pp-field-value">{value || '—'}</p>
    </div>
  )
}

// ── Toggle row ────────────────────────────────────────────────────────────────
function ToggleRow({ label, enabled, onChange }) {
  return (
    <div className="pp-toggle-row">
      <p className="pp-toggle-label">{label}</p>
      <button
        className={`pp-toggle ${enabled ? 'on' : 'off'}`}
        onClick={onChange}
        aria-pressed={!!enabled}
      >
        <div className="pp-toggle-knob" />
      </button>
    </div>
  )
}

function PatientProfile() {
  const navigate = useNavigate()
  const [profile, setProfile]       = useState(null)
  const [userId, setUserId]         = useState(null)
  const [authorized, setAuthorized] = useState(
    () => sessionStorage.getItem('userRole') === 'patient'
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

      if (sessionStorage.getItem('userRole') === 'patient') {
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
      if (role !== 'patient') {
        sessionStorage.removeItem('userRole')
        navigate('/', { replace: true })
        return
      }

      sessionStorage.setItem('userRole', 'patient')
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

  return (
    <div className="pp-layout">

      {/* ── Sidebar ── */}
      <aside className="pp-sidebar">

        <div className="pp-profile">
          <div className="pp-avatar">
            <IconUser />
          </div>
          <button className="pp-profile-name pp-profile-name--active" onClick={() => {}}>
            {displayName}
          </button>
          <span className="pp-profile-role">Patient</span>
        </div>

        <nav className="pp-nav">
          <div className="pp-nav-item" onClick={() => navigate('/patient-dashboard')}>
            <span className="pp-nav-icon-svg"><IconDashboard /></span>
            <span className="pp-nav-label">Dashboard</span>
          </div>
          <div className="pp-nav-item">
            <img className="pp-nav-icon" src={calendarIcon} alt="" />
            <span className="pp-nav-label">My Appointments</span>
          </div>
          <div className="pp-nav-item">
            <img className="pp-nav-icon" src={documentsIcon} alt="" />
            <span className="pp-nav-label">Medical Records</span>
          </div>
          <div className="pp-nav-item">
            <img className="pp-nav-icon" src={settingsIcon} alt="" />
            <span className="pp-nav-label">Settings</span>
          </div>
          <div className="pp-nav-item pp-nav-logout" onClick={handleLogout}>
            <img className="pp-nav-icon" src={logoutIcon} alt="" />
            <span className="pp-nav-label">Log Out</span>
          </div>
        </nav>

      </aside>

      {/* ── Main content ── */}
      <main className="pp-main">

        <button className="pp-back-btn" onClick={() => navigate('/patient-dashboard')}>
          <IconBack /> Dashboard
        </button>

        <h1 className="pp-heading">My Profile</h1>
        <p className="pp-subtitle">View and manage your personal information.</p>

        {/* ── Profile header card ── */}
        <div className="pp-header-card">
          <div className="pp-header-initials">{initials}</div>
          <div className="pp-header-info">
            <p className="pp-header-name">{displayName}</p>
            <p className="pp-header-username">{username}</p>
            <span className="pp-header-badge">Patient</span>
          </div>
          {/* TODO: wire up once edit profile flow is built */}
          <button className="pp-edit-btn" onClick={() => {}}>Edit Profile</button>
        </div>

        {/* ── Personal Information ── */}
        <p className="pp-section-label">PERSONAL INFORMATION</p>
        <div className="pp-divider" />
        <div className="pp-fields-grid">
          <InfoField label="FIRST NAME"    value={profile?.first_name} />
          <InfoField label="LAST NAME"     value={profile?.last_name} />
          <InfoField label="DISPLAY NAME"  value={profile?.display_name} />
          <InfoField label="USERNAME"      value={username} />
          <InfoField label="PHONE NUMBER"  value={profile?.phone_number} />
          <InfoField label="DATE OF BIRTH" value={formatDob(profile?.date_of_birth)} />
          <InfoField label="GENDER"        value={profile?.gender} />
          <InfoField label="MEMBER SINCE"  value={formatMemberSince(profile?.member_since)} />
        </div>

        {/* ── Insurance ── */}
        <p className="pp-section-label">INSURANCE</p>
        <div className="pp-divider" />
        <div className="pp-fields-grid">
          <InfoField label="INSURANCE PROVIDER" value={profile?.insurance_provider} />
          <InfoField label="MEMBER ID"           value={profile?.insurance_member_id} />
        </div>

        {/* ── Emergency Contact ── */}
        <p className="pp-section-label">EMERGENCY CONTACT</p>
        <div className="pp-divider" />
        <div className="pp-fields-grid">
          <InfoField label="CONTACT NAME"  value={profile?.emergency_contact_name} />
          <InfoField label="CONTACT PHONE" value={profile?.emergency_contact_phone} />
        </div>

        {/* ── Notifications ── */}
        <p className="pp-section-label">NOTIFICATIONS</p>
        <div className="pp-divider" />
        <div className="pp-toggles-grid">
          <ToggleRow label="Appointment Reminders" enabled={profile?.notify_appointment_reminders} onChange={() => handleToggle('notify_appointment_reminders')} />
          <ToggleRow label="Appointment Updates"   enabled={profile?.notify_appointment_updates}   onChange={() => handleToggle('notify_appointment_updates')} />
          <ToggleRow label="Messages"              enabled={profile?.notify_messages}              onChange={() => handleToggle('notify_messages')} />
        </div>

        {/* ── Preferences ── */}
        <p className="pp-section-label">PREFERENCES</p>
        <div className="pp-divider" />
        <div className="pp-fields-grid">
          <InfoField label="PREFERRED CONTACT METHOD" value={profile?.preferred_contact_method} />
          <InfoField label="PREFERRED LANGUAGE"       value={profile?.preferred_language} />
          <InfoField label="ACCESSIBILITY MODE"       value={profile?.accessibility_mode} />
        </div>

      </main>
    </div>
  )
}

export default PatientProfile
