// App.jsx — the root component. Defines all client-side routes.
// To add a new page:
//   1. Create a component in src/pages/
//   2. Import it here
//   3. Add a <Route path="..." element={<YourPage />} /> inside <Routes>
import { Routes, Route } from 'react-router-dom'
import Home from './pages/Home'
import ClosuresAdmin from './pages/ClosuresAdmin'
import AppointmentHistory from './pages/AppointmentHistory'
import Register from './pages/Register'
import Login from './pages/Login'
import RoleSelection from './pages/RoleSelection'
import PatientDetails from './pages/PatientDetails'
import DoctorDetails from './pages/DoctorDetails'
import AdminDetails from './pages/AdminDetails'
import OnboardingSuccess from './pages/OnboardingSuccess'
import PatientDashboard from './pages/PatientDashboard'
import DoctorDashboard from './pages/DoctorDashboard'
import AdminDashboard from './pages/AdminDashboard'
import PatientProfile from './pages/PatientProfile'
import DoctorProfile from './pages/DoctorProfile'
import AdminProfile from './pages/AdminProfile'
import AdminUsers from './pages/AdminUsers'
import AccountSettings from './pages/AccountSettings'

function App() {
  return (
    <Routes>
      {/* Each <Route> maps a URL path to a page component */}
      <Route path="/" element={<Home />} />
      <Route path="/admin/closures" element={<ClosuresAdmin />} />
      <Route path="/appointmenthistory" element={<AppointmentHistory />} />
      <Route path="/register" element={<Register />} />
      <Route path="/login" element={<Login />} />
      <Route path="/role-selection" element={<RoleSelection />} />
      <Route path="/patient-details" element={<PatientDetails />} />
      <Route path="/doctor-details" element={<DoctorDetails />} />
      <Route path="/admin-details" element={<AdminDetails />} />
      <Route path="/onboarding-success" element={<OnboardingSuccess />} />
      <Route path="/patient-dashboard" element={<PatientDashboard />} />
      <Route path="/doctor-dashboard" element={<DoctorDashboard />} />
      <Route path="/admin-dashboard" element={<AdminDashboard />} />
      <Route path="/patient-profile" element={<PatientProfile />} />
      <Route path="/doctor-profile" element={<DoctorProfile />} />
      <Route path="/admin-profile" element={<AdminProfile />} />
      <Route path="/admin/users" element={<AdminUsers />} />
      <Route path="/settings" element={<AccountSettings />} />
      {/* Add new routes below as the app grows */}
    </Routes>
  )
}

export default App