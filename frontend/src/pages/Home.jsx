// Home.jsx — the landing page rendered at the "/" route.
// Replace the contents of this component with actual UI as development progresses.
import { Link } from 'react-router-dom'

function Home() {
  return (
    <div>
      <h1>Medical Appointments</h1>
      <p>Welcome to the medical appointments system.</p>
      <p>
        <Link to="/appointmenthistory">View appointment history</Link>
      </p>
    </div>
  )
}

export default Home
