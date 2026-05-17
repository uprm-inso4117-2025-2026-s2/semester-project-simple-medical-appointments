// AppointmentHistory.jsx — displays appointment history fetched from the Flask backend.
import { useEffect, useState } from 'react'
import { getAllAppointmentHistory } from '../services/api'
import '../styles/AppointmentHistory.css'

function formatAppointmentDate(value) {
  if (!value) return 'Not scheduled'

  const parsed = new Date(value)
  if (Number.isNaN(parsed.getTime())) return value

  return parsed.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  })
}

function getStatusClass(status) {
  const normalized = String(status ?? '').trim().toLowerCase()

  if (normalized === 'confirmed') return 'confirmed'
  if (normalized === 'completed') return 'completed'
  if (normalized === 'cancelled') return 'cancelled'
  if (normalized === 'pending') return 'pending'

  return 'default'
}

function AppointmentHistory() {
  const [appointments, setAppointments] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    getAllAppointmentHistory()
      .then((data) => setAppointments(data))
      .catch((err) => setError(err.message ?? 'Failed to load appointment history'))
      .finally(() => setLoading(false))
  }, [])

  const confirmedCount = appointments.filter(
    (appointment) => String(appointment.status ?? '').toLowerCase() === 'confirmed'
  ).length

  const completedCount = appointments.filter(
    (appointment) => String(appointment.status ?? '').toLowerCase() === 'completed'
  ).length

  let content = null

  if (loading) {
    content = (
      <section className="ah-state-card" aria-live="polite">
        <div className="ah-loading-indicator" aria-hidden="true" />
        <h2 className="ah-state-title">Loading appointment history…</h2>
        <p className="ah-state-text">Pulling your recent and upcoming visits now.</p>
      </section>
    )
  } else if (error) {
    content = (
      <section className="ah-state-card ah-state-card-error" role="alert">
        <span className="ah-state-kicker">Something went wrong</span>
        <h2 className="ah-state-title">Unable to load appointment history</h2>
        <p className="ah-state-text">{error}</p>
      </section>
    )
  } else if (!appointments.length) {
    content = (
      <section className="ah-state-card">
        <span className="ah-state-kicker">No visits yet</span>
        <h2 className="ah-state-title">No appointments found</h2>
        <p className="ah-state-text">
          Once appointments are booked, they will appear here with their latest status.
        </p>
      </section>
    )
  } else {
    content = (
      <>
        <section className="ah-summary-grid" aria-label="Appointment summary">
          <article className="ah-summary-card">
            <span className="ah-summary-label">Total Appointments</span>
            <strong className="ah-summary-value">{appointments.length}</strong>
          </article>
          <article className="ah-summary-card">
            <span className="ah-summary-label">Confirmed</span>
            <strong className="ah-summary-value">{confirmedCount}</strong>
          </article>
          <article className="ah-summary-card">
            <span className="ah-summary-label">Completed</span>
            <strong className="ah-summary-value">{completedCount}</strong>
          </article>
        </section>

        <section className="ah-table-card">
          <div className="ah-table-scroll">
            <table className="ah-table">
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
                {appointments.map((appointment) => {
                  const statusClass = getStatusClass(appointment.status)

                  return (
                    <tr key={appointment.id}>
                      <td data-label="Patient ID">{appointment.patient_id ?? 'N/A'}</td>
                      <td data-label="Doctor">{appointment.doctor_name ?? 'Unassigned'}</td>
                      <td data-label="Clinic">{appointment.clinic_name ?? 'Unknown clinic'}</td>
                      <td data-label="Date & Time">
                        {formatAppointmentDate(appointment.appointment_datetime)}
                      </td>
                      <td data-label="Status">
                        <span className={`ah-status-pill ah-status-${statusClass}`}>
                          {appointment.status ?? 'Unknown'}
                        </span>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </section>
      </>
    )
  }

  return (
    <div className="ah-page">
      <main className="ah-shell">
        <header className="ah-header">
          <div>
            <p className="ah-eyebrow">Patient Portal</p>
            <h1 className="ah-title">Appointment History</h1>
            <p className="ah-subtitle">
              Review your bookings, check statuses, and keep track of past visits.
            </p>
          </div>
        </header>

        {content}
      </main>
    </div>
  )
}

export default AppointmentHistory
