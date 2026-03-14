// AppointmentHistory.jsx — displays a user's appointment history.
// This page fetches data from the backend and renders it in a table.
import { useEffect, useState } from 'react'
import { getAppointmentHistory } from '../services/api'

function AppointmentHistory() {
  const [appointments, setAppointments] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    getAppointmentHistory(1)
      .then((data) => {
        setAppointments(data)
        setLoading(false)
      })
      .catch((err) => {
        setError(err.message)
        setLoading(false)
      })
  }, [])

  if (loading) {
    return <p>Loading appointment history…</p>
  }

  if (error) {
    return <p style={{ color: 'red' }}>Error: {error}</p>
  }

  if (!appointments.length) {
    return <p>No appointments found.</p>
  }

  return (
    <div>
      <h1>Appointment History</h1>
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>User ID</th>
            <th>Date</th>
            <th>Time</th>
            <th>Clinic</th>
            <th>Doctor</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {appointments.map((appt) => (
            <tr key={appt.id}>
              <td>{appt.id}</td>
              <td>{appt.user_id}</td>
              <td>{appt.appointment_date}</td>
              <td>{appt.appointment_time}</td>
              <td>{appt.clinic_id}</td>
              <td>{appt.doctor_id}</td>
              <td>{appt.status}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default AppointmentHistory
