// AdminProfile.jsx — Admin profile page at "/admin-profile".
// All data fetched from GET /api/profile/:userId which returns fields from:
//   profiles, profile_settings tables.
// Read-only — no profile editing.

import { useEffect, useState } from 'react'
import { useNavigate, Navigate } from 'react-router-dom'
import { supabase } from '../lib/supabaseClient'
import { getProfile } from '../services/api'

import calendarIcon from '../assets/calendar_icon.svg'
import settingsIcon from '../assets/settings_icon.svg'
import logoutIcon   from '../assets/logout_icon.svg'

import '../styles/adminProfile.css'

// ── Inline icons ──────────────────────────────────────────────────────────────
const IconDashboard = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <rect x="3" y="3" width="7" height="7" rx="1"/>
    <rect x="14" y="3" width="7" height="7" rx="1"/>
    <rect x="3" y="14" width="7" height="7" rx="1"/>
    <rect x="14" y="14" width="7" height="7" rx="1"/>
  </svg>
)
const IconManagement = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <rect x="3" y="3" width="18" height="5" rx="1"/>
    <rect x="3" y="11" width="18" height="5" rx="1"/>
    <rect x="3" y="19" width="18" height="2" rx="1"/>
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

function getInitials(firstName, lastName) {
  const f = firstName?.[0] ?? ''
  const l = lastName?.[0] ?? ''
  return (f + l).toUpperCase() || '?'
}

function InfoField({ label, value }) {
  return (
    <div className="ap-field">
      <p className="ap-field-label">{label}</p>
      <p className="ap-field-value">{value || '—'}</p>
    </div>
  )
}

function AdminProfile() {
  const navigate = useNavigate()
  const [profile, setProfile]       = useState(null)
  const [authorized, setAuthorized] = useState(
    () => sessionStorage.getItem('userRole') === 'admin'
  )

  useEffect(() => {
    const checkAccess = async () => {
      const { data: { session } } = await supabase.auth.getSession()
      if (!session) {
        sessionStorage.removeItem('userRole')
        navigate('/login', { replace: true })
        return
      }

      if (sessionStorage.getItem('userRole') === 'admin') {
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
      if (role !== 'admin') {
        sessionStorage.removeItem('userRole')
        navigate('/', { replace: true })
        return
      }

      sessionStorage.setItem('userRole', 'admin')
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

  if (!authorized) {
    const cached = sessionStorage.getItem('userRole')
    return <Navigate to={cached ? '/' : '/login'} replace />
  }

  const displayName = profile?.display_name ?? profile?.name ?? '…'
  const initials    = getInitials(profile?.first_name, profile?.last_name)
  const username    = profile?.username ? `@${profile.username}` : '—'

  return (
    <div className="ap-layout">

      {/* ── Sidebar ── */}
      <aside className="ap-sidebar">

        <div className="ap-profile">
          <div className="ap-avatar">
            <IconUser />
          </div>
          <button className="ap-profile-name ap-profile-name--active" onClick={() => {}}>
            {displayName}
          </button>
          <span className="ap-profile-role">Admin</span>
        </div>

        <nav className="ap-nav">
          <div className="ap-nav-item" onClick={() => navigate('/admin-dashboard')}>
            <span className="ap-nav-icon-svg"><IconDashboard /></span>
            <span className="ap-nav-label">Dashboard</span>
          </div>
          <div className="ap-nav-item" onClick={() => {}}>
            <span className="ap-nav-icon-svg"><IconManagement /></span>
            <span className="ap-nav-label">Management</span>
          </div>
          <div className="ap-nav-item">
            <img className="ap-nav-icon" src={calendarIcon} alt="" />
            <span className="ap-nav-label">Appointments</span>
          </div>
          <div className="ap-nav-item">
            <img className="ap-nav-icon" src={settingsIcon} alt="" />
            <span className="ap-nav-label">Settings</span>
          </div>
          <div className="ap-nav-item ap-nav-logout" onClick={handleLogout}>
            <img className="ap-nav-icon" src={logoutIcon} alt="" />
            <span className="ap-nav-label">Log Out</span>
          </div>
        </nav>

      </aside>

      {/* ── Main content ── */}
      <main className="ap-main">

        <button className="ap-back-btn" onClick={() => navigate('/admin-dashboard')}>
          <IconBack /> Dashboard
        </button>

        <h1 className="ap-heading">My Profile</h1>
        <p className="ap-subtitle">Clinic administrator account overview.</p>

        {/* ── Profile header card ── */}
        <div className="ap-header-card">
          <div className="ap-header-initials">{initials}</div>
          <div className="ap-header-info">
            <p className="ap-header-name">{displayName}</p>
            <p className="ap-header-username">{username}</p>
            <span className="ap-header-badge">Admin</span>
          </div>
        </div>

        {/* ── Role & Permissions ── */}
        <p className="ap-section-label">ROLE &amp; PERMISSIONS</p>
        <div className="ap-divider" />
        <div className="ap-fields-grid">
          <InfoField label="ROLE"             value="System Administrator" />
          <InfoField label="ROLE DESCRIPTION" value="Full access to clinic operations and system configuration" />
        </div>

        {/* ── Preferences ── */}
        <p className="ap-section-label">PREFERENCES</p>
        <div className="ap-divider" />
        <div className="ap-fields-grid">
          <InfoField label="PREFERRED CONTACT METHOD" value={profile?.preferred_contact_method} />
          <InfoField label="PREFERRED LANGUAGE"       value={profile?.preferred_language} />
          <InfoField label="ACCESSIBILITY MODE"       value={profile?.accessibility_mode} />
        </div>

      </main>
    </div>
  )
}

export default AdminProfile
