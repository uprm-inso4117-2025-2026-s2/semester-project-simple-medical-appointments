// DoctorDashboard.jsx — Doctor dashboard at "/doctor-dashboard".
// Profile name fetched from GET /api/profile/:userId (returns display_name as `name`).
// Specialty fetched from same endpoint via JOIN on providers table.
// Schedule is MOCKED — replace MOCK_SCHEDULE once a backend endpoint returns
// enriched data via JOINs on appointments + patients + profiles (patient display_name).
// Real schema: id, patient_id, doctor_id, clinic_id, appointment_datetime, status, notes
// Status values: 'pending' | 'confirmed' | 'cancelled' | 'completed'

import { useEffect, useState } from 'react'
import { useNavigate, Navigate } from 'react-router-dom'
import { supabase } from '../lib/supabaseClient'
import { getProfile } from '../services/api'

import calendarIcon from '../assets/calendar_icon.svg'
import settingsIcon from '../assets/settings_icon.svg'
import logoutIcon   from '../assets/logout_icon.svg'

import '../styles/doctorDashboard.css'

// ── Mock schedule ─────────────────────────────────────────────────────────────
// TODO: replace with real API call once an endpoint returns enriched schedule data.
// Fields mirror what a JOIN on appointments + profiles (patient display_name) would return.
const MOCK_SCHEDULE = [
  { id: '1', patientName: 'Maria Gonzalez', appointment_datetime: '2026-04-01T09:00:00-04:00', status: 'confirmed' },
  { id: '2', patientName: 'Carlos Rivera',  appointment_datetime: '2026-04-01T10:30:00-04:00', status: 'pending'   },
  { id: '3', patientName: 'Ana Reyes',      appointment_datetime: '2026-04-01T12:00:00-04:00', status: 'cancelled' },
]

const STATUS_CONFIG = {
  confirmed:  { label: 'Confirmed',  dotColor: '#248daa' },
  pending:    { label: 'Pending',    dotColor: '#185fa5' },
  completed:  { label: 'Completed',  dotColor: '#888'    },
  cancelled:  { label: 'Cancelled',  dotColor: '#ba7517' },
}

function formatDatetime(iso) {
  const d = new Date(iso)
  return d.toLocaleString('en-US', { month: 'short', day: 'numeric', year: 'numeric', hour: 'numeric', minute: '2-digit' })
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

function DoctorDashboard() {
  const navigate = useNavigate()
  const [profile, setProfile]       = useState(null)
  // Pre-authorize immediately if the role is already cached from a previous visit
  const [authorized, setAuthorized] = useState(
    () => sessionStorage.getItem('userRole') === 'doctor'
  )

  useEffect(() => {
    const checkAccess = async () => {
      // getSession reads from local storage — no network request, instant
      const { data: { session } } = await supabase.auth.getSession()
      if (!session) {
        sessionStorage.removeItem('userRole')
        navigate('/login', { replace: true })
        return
      }

      // If already cached, skip the DB role check and just fetch profile
      if (sessionStorage.getItem('userRole') === 'doctor') {
        setAuthorized(true)
        try {
          const prof = await getProfile(session.user.id)
          setProfile(prof)
        } catch {}
        return
      }

      // No cache — verify role against DB
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
      } catch {
        // profile fetch failed — name falls back to placeholder
      }
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
  const firstName   = displayName !== '…' ? displayName.split(' ')[0] : '…'
  // TODO: specialty returned by GET /api/profile/:userId once doctor_profiles JOIN is added
  const specialty   = profile?.specialty ?? ''
  const todayCount  = MOCK_SCHEDULE.length

  return (
    <div className="ddb-layout">

      {/* ── Sidebar ── */}
      <aside className="ddb-sidebar">

        <div className="ddb-profile">
          <div className="ddb-avatar">
            <IconUser />
          </div>
          <button className="ddb-profile-name" onClick={() => navigate('/doctor-profile')}>
            {displayName}
          </button>
          {specialty && <span className="ddb-profile-role">{specialty}</span>}
          {!specialty && <span className="ddb-profile-role">Doctor</span>}
        </div>

        <nav className="ddb-nav">
          <div className="ddb-nav-item active">
            <span className="ddb-nav-icon-svg"><IconDashboard /></span>
            <span className="ddb-nav-label">Dashboard</span>
          </div>
          <div className="ddb-nav-item">
            <img className="ddb-nav-icon" src={calendarIcon} alt="" />
            <span className="ddb-nav-label">My Appointments</span>
          </div>
          <div className="ddb-nav-item">
            <img className="ddb-nav-icon" src={settingsIcon} alt="" />
            <span className="ddb-nav-label">Settings</span>
          </div>
          <div className="ddb-nav-item ddb-nav-logout" onClick={handleLogout}>
            <img className="ddb-nav-icon" src={logoutIcon} alt="" />
            <span className="ddb-nav-label">Log Out</span>
          </div>
        </nav>

      </aside>

      {/* ── Main content ── */}
      <main className="ddb-main">

        <button className="ddb-back-btn" onClick={() => navigate('/')}>
          <IconBack /> Home
        </button>

        <h1 className="ddb-welcome">Welcome, Dr. {firstName}</h1>
        <p className="ddb-subtitle">You have {todayCount} appointments for today.</p>

        <div className="ddb-stats-card">
          <p className="ddb-stats-label">Upcoming Appointments</p>
          <p className="ddb-stats-count">2</p>
          <p className="ddb-stats-next">Next: Tomorrow, 9:00 AM</p>
        </div>

        <p className="ddb-section-heading">Today's Schedule</p>

        <div className="ddb-schedule-list">
          {MOCK_SCHEDULE.map(appt => {
            const { dotColor } = STATUS_CONFIG[appt.status] ?? { dotColor: '#ccc' }
            return (
              <div key={appt.id} className="ddb-schedule-card">
                <span className="ddb-schedule-dot" style={{ background: dotColor }} />
                <div className="ddb-schedule-info">
                  <p className="ddb-schedule-patient">{appt.patientName}</p>
                  <p className="ddb-schedule-time">{formatDatetime(appt.appointment_datetime)}</p>
                </div>
              </div>
            )
          })}
        </div>

      </main>
    </div>
  )
}

export default DoctorDashboard
