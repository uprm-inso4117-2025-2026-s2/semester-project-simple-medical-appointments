// App.jsx — the root component. Defines all client-side routes.
// To add a new page:
//   1. Create a component in src/pages/
//   2. Import it here
//   3. Add a <Route path="..." element={<YourPage />} /> inside <Routes>
import { Routes, Route } from 'react-router-dom'
import Home from './pages/Home'
import AppointmentHistory from './pages/AppointmentHistory'
import Register from './pages/Register'
import Login from './pages/Login'

function App() {
  return (
    <Routes>
      {/* Each <Route> maps a URL path to a page component */}
      <Route path="/" element={<Home />} />
      <Route path="/appointmenthistory" element={<AppointmentHistory />} />
      <Route path="/register" element={<Register />} />
      <Route path="/login" element={<Login />} />
      {/* Add new routes below as the app grows */}
    </Routes>
  )
}

export default App
