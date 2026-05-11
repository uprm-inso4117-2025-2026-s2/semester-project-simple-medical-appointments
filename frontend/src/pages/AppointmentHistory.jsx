// AppointmentHistory.jsx — displays appointment history fetched from the Flask backend.
import { useEffect, useState } from 'react'
import { getAllAppointmentHistory } from '../services/api'

function AppointmentHistory() {
  const [appointments, setAppointments] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    getAllAppointmentHistory()
      .then(data => setAppointments(data))
      .catch(err => setError(err.message ?? 'Failed to load appointment history'))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <p>Loading appointment history…</p>
  if (error)   return <p style={{ color: 'red' }}>Error: {error}</p>
  if (!appointments.length) return <p>No appointments found.</p>

  return (
    <div>
      <h1>Appointment History</h1>
      <table>
        <thead>
          <tr>
            <th>Patient ID</th>
            <th>Doctor</th>
            <th>Clinic</th>
            <th>Date &amp; Time</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {appointments.map((appt) => (
            <tr key={appt.id}>
              <td>{appt.patient_id ?? 'N/A'}</td>
              <td>{appt.doctor_name}</td>
              <td>{appt.clinic_name}</td>
              <td>{new Date(appt.appointment_datetime).toLocaleString()}</td>
              <td>{appt.status}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default AppointmentHistory