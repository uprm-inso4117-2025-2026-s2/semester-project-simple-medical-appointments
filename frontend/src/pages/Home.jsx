import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { supabase } from '../lib/supabaseClient'
import medicalIcon from '../assets/medicalPng.png'
import '../styles/home.css'

const IconCalendar = () => (
  <svg viewBox="0 0 24 24">
    <rect x="3" y="4" width="18" height="18" rx="2"/>
    <line x1="16" y1="2" x2="16" y2="6"/>
    <line x1="8" y1="2" x2="8" y2="6"/>
    <line x1="3" y1="10" x2="21" y2="10"/>
  </svg>
)

const IconClipboard = () => (
  <svg viewBox="0 0 24 24">
    <path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/>
    <rect x="8" y="2" width="8" height="4" rx="1"/>
    <line x1="8" y1="13" x2="16" y2="13"/>
    <line x1="8" y1="17" x2="12" y2="17"/>
  </svg>
)

const IconPlus = () => (
  <svg viewBox="0 0 24 24">
    <circle cx="12" cy="12" r="9"/>
    <line x1="12" y1="8" x2="12" y2="16"/>
    <line x1="8" y1="12" x2="16" y2="12"/>
  </svg>
)

const DASHBOARD_ROUTES = {
  patient: '/patient-dashboard',
  doctor: '/doctor-dashboard',
  admin:  '/admin-dashboard',
}

function Home() {
  const navigate = useNavigate()
  const [userEmail, setUserEmail] = useState('')
  const [userRole, setUserRole] = useState(null)

  useEffect(() => {
    supabase.auth.getUser().then(async ({ data }) => {
      if (!data?.user) {
        navigate('/login')
        return
      }

      setUserEmail(data.user.email)

      const { data: roleRows } = await supabase
        .from('user_roles')
        .select('roles(name)')
        .eq('user_id', data.user.id)

      if (roleRows?.length) {
        const role = roleRows[0]?.roles?.name ?? null
        setUserRole(role)
        if (role) sessionStorage.setItem('userRole', role)
      }
    })
  }, [navigate])

  const handleLogout = async () => {
    sessionStorage.removeItem('userRole')
    await supabase.auth.signOut()
    navigate('/login')
  }

  const dashboardRoute = userRole ? (DASHBOARD_ROUTES[userRole] ?? null) : null

  return (
    <div className="home-page">
      <nav className="home-nav">
        <div className="home-nav-brand">
          <img src={medicalIcon} alt="logo" />
          <span>Medical Appointments</span>
        </div>
        <div className="home-nav-actions">
          <span>{userEmail}</span>
          <button className="home-nav-logout" onClick={handleLogout}>
            Log out
          </button>
        </div>
      </nav>

      <main className="home-main">
        <div className="home-welcome">
          <h1>Welcome back!</h1>
          <p>What would you like to do today?</p>
        </div>

        <div className="home-cards">
          <Link to="/appointmenthistory" className="home-card">
            <div className="home-card-icon"><IconCalendar /></div>
            <p className="home-card-title">My Appointments</p>
            <p className="home-card-desc">
              View your full appointment history and upcoming visits.
            </p>
            <span className="home-card-arrow">View all →</span>
          </Link>

          <div className="home-card disabled">
            <div className="home-card-icon"><IconPlus /></div>
            <p className="home-card-title">Book Appointment</p>
            <p className="home-card-desc">
              Schedule a new appointment with a doctor or clinic.
            </p>
            <span className="home-card-badge">Coming soon</span>
          </div>

          <div className="home-card disabled">
            <div className="home-card-icon"><IconClipboard /></div>
            <p className="home-card-title">Patient Form</p>
            <p className="home-card-desc">
              Submit your symptoms, allergies, and current medications.
            </p>
            <span className="home-card-badge">Coming soon</span>
          </div>
        </div>

        <button
          className="home-dashboard-btn"
          onClick={() => dashboardRoute && navigate(dashboardRoute)}
          disabled={!dashboardRoute}
        >
          Go to Dashboard
        </button>
      </main>

      <p>
        <Link to="/appointmenthistory">
          View appointment history
        </Link>
      </p>
    </div>
  )
}

export default Home