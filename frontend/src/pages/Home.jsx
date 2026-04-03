// Home.jsx — the landing page rendered at the "/" route.
// Replace the contents of this component with actual UI as development progresses.
import { Link } from 'react-router-dom'
import ServiceCatalog from './ServiceCatalog'

function Home() {
  return (
    <div className="home-page">
      <nav className="home-nav">
        <div className="home-nav-brand">
          <img src={medicalIcon} alt="Simple Medical Appointments" />
          <span>Simple Medical Appointments</span>
        </div>
        <div className="home-nav-user">
          <span className="home-nav-email">{userEmail}</span>
          <button className="home-nav-settings" onClick={() => navigate('/settings')}>Settings</button>
          <button className="home-nav-logout" onClick={handleLogout}>Log out</button>
        </div>
      </nav>

      <ServiceCatalog />

      <p>
        <Link to="/appointmenthistory">
          View appointment history
        </Link>
      </p>
    </div>
  )
}

export default Home
