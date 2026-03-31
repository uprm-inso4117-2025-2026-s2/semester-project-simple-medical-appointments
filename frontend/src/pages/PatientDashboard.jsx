// PatientDashboard.jsx — Patient dashboard at "/patient-dashboard".
// Profile name fetched from GET /api/profile/:userId (returns display_name as `name`).
// Appointments are MOCKED — replace MOCK_APPOINTMENTS once a backend endpoint
// returns enriched data (doctor name, specialty) via JOINs on appointments + providers + profiles.
// Status values match the DB: 'scheduled' | 'completed' | 'cancelled'

import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { supabase } from '../lib/supabaseClient'
import { getProfile } from '../services/api'

import calendarIcon  from '../assets/calendar_icon.svg'
import documentsIcon from '../assets/documents_icon.svg'
import logoutIcon    from '../assets/logout_icon.svg'
import settingsIcon  from '../assets/settings_icon.svg'

import '../styles/patientDashboard.css'

// ── Mock appointments ─────────────────────────────────────────────────────────
// TODO: replace with real API call once an endpoint returns enriched appointment data
const MOCK_APPOINTMENTS = [
  {
    id: 1,
    doctorName: 'Dr. Elena Torres',
    specialty: 'Cardiology',
    dateLabel: 'Tomorrow · 9:00 AM',
    status: 'scheduled',
  },
  {
    id: 2,
    doctorName: 'Dr. James Ruiz',
    specialty: 'General Practice',
    dateLabel: 'Mar 24, 2026 · 2:30 PM',
    status: 'cancelled',
  },
]

const STATUS_CONFIG = {
  scheduled: { label: 'Scheduled', dotColor: '#248DAA' },
  completed:  { label: 'Completed', dotColor: '#888'    },
  cancelled:  { label: 'Cancelled', dotColor: '#BA7517' },
}

// ── Inline icons (no asset file) ──────────────────────────────────────────────
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

function PatientDashboard() {
  const navigate = useNavigate()
  const [profile, setProfile] = useState(null)

  useEffect(() => {
    supabase.auth.getUser().then(async ({ data }) => {
      if (!data?.user) {
        navigate('/login')
        return
      }
      try {
        const prof = await getProfile(data.user.id)
        setProfile(prof)
      } catch {
        // profile fetch failed — name falls back to placeholder
      }
    })
  }, [navigate])

  const handleLogout = async () => {
    await supabase.auth.signOut()
    navigate('/login')
  }

  const displayName  = profile?.name ?? '…'
  const firstName    = displayName !== '…' ? displayName.split(' ')[0] : '…'
  const upcomingCount = MOCK_APPOINTMENTS.filter(a => a.status === 'scheduled').length

  return (
    <div className="pdb-layout">

      {/* ── Sidebar ── */}
      <aside className="pdb-sidebar">

        <div className="pdb-profile">
          <div className="pdb-avatar">
            <IconUser />
          </div>
          {/* TODO: navigate to /profile once that page is built */}
          <button className="pdb-profile-name" onClick={() => {}}>
            {displayName}
          </button>
          <span className="pdb-profile-role">Patient</span>
        </div>

        <nav className="pdb-nav">
          <div className="pdb-nav-item active">
            <span className="pdb-nav-icon-svg"><IconDashboard /></span>
            <span className="pdb-nav-label">Dashboard</span>
          </div>
          <div className="pdb-nav-item">
            <img className="pdb-nav-icon" src={calendarIcon} alt="" />
            <span className="pdb-nav-label">My Appointments</span>
          </div>
          <div className="pdb-nav-item">
            <img className="pdb-nav-icon" src={documentsIcon} alt="" />
            <span className="pdb-nav-label">Medical Records</span>
          </div>
          <div className="pdb-nav-item">
            <img className="pdb-nav-icon" src={settingsIcon} alt="" />
            <span className="pdb-nav-label">Settings</span>
          </div>
          <div className="pdb-nav-item pdb-nav-logout" onClick={handleLogout}>
            <img className="pdb-nav-icon" src={logoutIcon} alt="" />
            <span className="pdb-nav-label">Log Out</span>
          </div>
        </nav>

      </aside>

      {/* ── Main content ── */}
      <main className="pdb-main">

        <button className="pdb-back-btn" onClick={() => navigate('/')}>
          <IconBack /> Home
        </button>

        <h1 className="pdb-welcome">Welcome, {firstName}</h1>
        <p className="pdb-subtitle">Here is your health overview for today.</p>

        <div className="pdb-stats-card">
          <p className="pdb-stats-label">Upcoming Appointments</p>
          <p className="pdb-stats-count">{upcomingCount}</p>
          <p className="pdb-stats-next">Next: Tomorrow, 9:00 AM</p>
        </div>

        <p className="pdb-section-heading">Upcoming Appointments</p>

        <div className="pdb-apt-list">
          {MOCK_APPOINTMENTS.map(apt => {
            const { label, dotColor } = STATUS_CONFIG[apt.status] ?? { label: apt.status, dotColor: '#ccc' }
            return (
              <div key={apt.id} className="pdb-apt-card">
                <span className="pdb-apt-dot" style={{ background: dotColor }} />
                <div className="pdb-apt-info">
                  <p className="pdb-apt-doctor">{apt.doctorName} — {apt.specialty}</p>
                  <p className="pdb-apt-date">{apt.dateLabel}</p>
                </div>
                <span className={`pdb-apt-badge ${apt.status}`}>{label}</span>
              </div>
            )
          })}
        </div>

        <button className="pdb-book-btn" disabled>+ Book New Appointment</button>

      </main>
    </div>
  )
}

export default PatientDashboard
