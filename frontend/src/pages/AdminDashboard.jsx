// AdminDashboard.jsx — Admin dashboard at "/admin-dashboard".
// Profile name fetched from GET /api/profile/:userId (returns display_name as `name`).
// All stats and appointments are MOCKED — replace once backend endpoints exist:
//   - Appointments Today: COUNT appointments WHERE DATE(appointment_datetime) = today
//   - Active Doctors:     COUNT providers
//   - Active Clinics:     COUNT clinics
//   - Recent Appointments: appointments JOIN profiles (patient display_name)
//                          + providers→profiles (doctor display_name) + clinics (name)
// Appointments schema: id, patient_id, doctor_id, clinic_id, appointment_datetime, status, notes
// Status values: 'pending' | 'confirmed' | 'cancelled' | 'completed'

import { useEffect, useState } from 'react'
import { useNavigate, Navigate } from 'react-router-dom'
import { supabase } from '../lib/supabaseClient'
import { getProfile } from '../services/api'

import calendarIcon from '../assets/calendar_icon.svg'
import settingsIcon from '../assets/settings_icon.svg'
import logoutIcon   from '../assets/logout_icon.svg'

import '../styles/adminDashboard.css'

// ── Mock stats ────────────────────────────────────────────────────────────────
// TODO: replace with real API calls
const MOCK_STATS = {
  appointmentsToday: 38,
  activeDoctors: 12,
  activeClinics: 3,
}


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

function AdminDashboard() {
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

  const displayName = profile?.name ?? '…'

  return (
    <div className="adb-layout">

      {/* ── Sidebar ── */}
      <aside className="adb-sidebar">

        <div className="adb-profile">
          <div className="adb-avatar">
            <IconUser />
          </div>
          <button className="adb-profile-name" onClick={() => {}}>
            {displayName}
          </button>
          <span className="adb-profile-role">Admin</span>
        </div>

        <nav className="adb-nav">
          <div className="adb-nav-item active">
            <span className="adb-nav-icon-svg"><IconDashboard /></span>
            <span className="adb-nav-label">Dashboard</span>
          </div>
          {/* TODO: navigate to /admin/management once that page is built */}
          <div className="adb-nav-item" onClick={() => {}}>
            <span className="adb-nav-icon-svg"><IconManagement /></span>
            <span className="adb-nav-label">Management</span>
          </div>
          <div className="adb-nav-item">
            <img className="adb-nav-icon" src={calendarIcon} alt="" />
            <span className="adb-nav-label">Appointments</span>
          </div>
          <div className="adb-nav-item">
            <img className="adb-nav-icon" src={settingsIcon} alt="" />
            <span className="adb-nav-label">Settings</span>
          </div>
          <div className="adb-nav-item adb-nav-logout" onClick={handleLogout}>
            <img className="adb-nav-icon" src={logoutIcon} alt="" />
            <span className="adb-nav-label">Log Out</span>
          </div>
        </nav>

      </aside>

      {/* ── Main content ── */}
      <main className="adb-main">

        <button className="adb-back-btn" onClick={() => navigate('/')}>
          <IconBack /> Home
        </button>

        <h1 className="adb-welcome">Welcome, {displayName}</h1>
        <p className="adb-subtitle">Here is your clinic overview.</p>

        <div className="adb-stats-row">
          <div className="adb-stats-card">
            <p className="adb-stats-label">Appointments Today</p>
            <p className="adb-stats-count">{MOCK_STATS.appointmentsToday}</p>
            <p className="adb-stats-sub">Across all doctors</p>
          </div>
          <div className="adb-stats-card">
            <p className="adb-stats-label">Active Doctors</p>
            <p className="adb-stats-count">{MOCK_STATS.activeDoctors}</p>
            {/* TODO: link to /admin/doctors once that page is built */}
            <p className="adb-stats-link">Manage Doctors</p>
          </div>
          <div className="adb-stats-card">
            <p className="adb-stats-label">Active Clinics</p>
            <p className="adb-stats-count">{MOCK_STATS.activeClinics}</p>
            {/* TODO: link to /admin/clinics once that page is built */}
            <p className="adb-stats-link">Manage Clinics</p>
          </div>
        </div>


      </main>
    </div>
  )
}

export default AdminDashboard
