// AppointmentHistory.jsx — displays appointment history fetched from the Flask backend.
import { useEffect, useState } from 'react'
import { getAllAppointmentHistory, getAvailableSlots, rescheduleAppointment } from '../services/api'
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

/** Returns true if an appointment can be rescheduled. */
function isReschedulable(status) {
  const s = String(status ?? '').trim().toLowerCase()
  return s === 'pending' || s === 'confirmed'
}

// ---------------------------------------------------------------------------
// RescheduleModal
// ---------------------------------------------------------------------------

function RescheduleModal({ appointment, onClose, onSuccess }) {
  const today = new Date().toISOString().split('T')[0]

  const [selectedDate, setSelectedDate] = useState('')
  const [slots, setSlots] = useState([])
  const [slotsLoading, setSlotsLoading] = useState(false)
  const [slotsError, setSlotsError] = useState(null)
  const [selectedSlot, setSelectedSlot] = useState(null)
  const [submitting, setSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState(null)

  // Fetch available slots whenever the date changes.
  useEffect(() => {
    if (!selectedDate || !appointment.doctor_id) return

    setSlotsLoading(true)
    setSlotsError(null)
    setSlots([])
    setSelectedSlot(null)

    getAvailableSlots(appointment.doctor_id, selectedDate)
      .then((data) => setSlots(data.slots ?? []))
      .catch((err) => setSlotsError(err.message ?? 'Could not load slots'))
      .finally(() => setSlotsLoading(false))
  }, [selectedDate, appointment.doctor_id])

  async function handleConfirm() {
    if (!selectedSlot) return
    setSubmitting(true)
    setSubmitError(null)

    // Build ISO 8601: "2025-06-15T09:00:00"
    const newDatetime = `${selectedDate}T${selectedSlot.start_time}:00`

    try {
      await rescheduleAppointment(appointment.id, newDatetime)
      onSuccess(newDatetime)
    } catch (err) {
      // The api.js request helper surfaces the backend's message directly.
      setSubmitError(err.message ?? 'Rescheduling failed. Please try again.')
      setSubmitting(false)
    }
  }

  const missingDoctor = !appointment.doctor_id

  return (
    <div className="ah-modal-backdrop" role="dialog" aria-modal="true" aria-label="Reschedule appointment">
      <div className="ah-modal">
        <header className="ah-modal-header">
          <h2 className="ah-modal-title">Reschedule Appointment</h2>
          <button className="ah-modal-close" onClick={onClose} aria-label="Close" disabled={submitting}>
            ✕
          </button>
        </header>

        <div className="ah-modal-body">
          <p className="ah-modal-hint">
            Current appointment:{' '}
            <strong>{formatAppointmentDate(appointment.appointment_datetime)}</strong>
          </p>

          {missingDoctor ? (
            <p className="ah-modal-slots-error">
              This appointment has no assigned doctor, so it cannot be rescheduled.
            </p>
          ) : (
            <>
              {/* Step 1 — pick a date */}
              <label className="ah-modal-label" htmlFor="reschedule-date">
                Select a new date
              </label>
              <input
                id="reschedule-date"
                type="date"
                className="ah-modal-date-input"
                min={today}
                value={selectedDate}
                onChange={(e) => setSelectedDate(e.target.value)}
                disabled={submitting}
              />

              {/* Step 2 — pick a slot */}
              {selectedDate && (
                <div className="ah-modal-slots-section">
                  <p className="ah-modal-label">Select a time slot</p>

                  {slotsLoading && (
                    <p className="ah-modal-slots-loading">Loading available slots…</p>
                  )}

                  {slotsError && (
                    <p className="ah-modal-slots-error">{slotsError}</p>
                  )}

                  {!slotsLoading && !slotsError && slots.length === 0 && (
                    <p className="ah-modal-slots-empty">No available slots for this date.</p>
                  )}

                  {!slotsLoading && slots.length > 0 && (
                    <div className="ah-slots-grid">
                      {slots.map((slot) => {
                        const isSelected =
                          selectedSlot?.start_time === slot.start_time
                        return (
                          <button
                            key={slot.start_time}
                            type="button"
                            className={`ah-slot-btn${isSelected ? ' ah-slot-btn--selected' : ''}`}
                            onClick={() => setSelectedSlot(slot)}
                            disabled={submitting}
                          >
                            {slot.start_time}
                          </button>
                        )
                      })}
                    </div>
                  )}
                </div>
              )}
            </>
          )}

          {/* Error from the confirm call */}
          {submitError && (
            <p className="ah-modal-submit-error" role="alert">{submitError}</p>
          )}
        </div>

        <footer className="ah-modal-footer">
          <button
            className="ah-modal-btn ah-modal-btn--secondary"
            onClick={onClose}
            disabled={submitting}
          >
            Cancel
          </button>
          <button
            className="ah-modal-btn ah-modal-btn--primary"
            onClick={handleConfirm}
            disabled={!selectedSlot || submitting || missingDoctor}
          >
            {submitting ? 'Rescheduling…' : 'Confirm reschedule'}
          </button>
        </footer>
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// AppointmentHistory
// ---------------------------------------------------------------------------

function AppointmentHistory() {
  const [appointments, setAppointments] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // Reschedule modal state
  const [reschedulingAppt, setReschedulingAppt] = useState(null)
  const [successMessage, setSuccessMessage] = useState(null)

  useEffect(() => {
    getAllAppointmentHistory()
      .then((data) => setAppointments(data))
      .catch((err) => setError(err.message ?? 'Failed to load appointment history'))
      .finally(() => setLoading(false))
  }, [])

  function handleRescheduleClick(appointment) {
    setSuccessMessage(null)
    setReschedulingAppt(appointment)
  }

  function handleModalClose() {
    setReschedulingAppt(null)
  }

  function handleRescheduleSuccess(newDatetime) {
    // Optimistically update the appointment in the list
    setAppointments((prev) =>
      prev.map((appt) =>
        appt.id === reschedulingAppt.id
          ? { ...appt, appointment_datetime: newDatetime }
          : appt
      )
    )
    setReschedulingAppt(null)
    setSuccessMessage('Appointment rescheduled successfully.')

    // Clear the success message after 5 s
    setTimeout(() => setSuccessMessage(null), 5000)
  }

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
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {appointments.map((appointment) => {
                  const statusClass = getStatusClass(appointment.status)
                  const canReschedule = isReschedulable(appointment.status)

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
                      <td data-label="Actions">
                        {canReschedule ? (
                          <button
                            className="ah-reschedule-btn"
                            onClick={() => handleRescheduleClick(appointment)}
                          >
                            Reschedule
                          </button>
                        ) : (
                          <span className="ah-no-action">—</span>
                        )}
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

        {successMessage && (
          <div className="ah-success-banner" role="status">
            {successMessage}
          </div>
        )}

        {content}
      </main>

      {reschedulingAppt && (
        <RescheduleModal
          appointment={reschedulingAppt}
          onClose={handleModalClose}
          onSuccess={handleRescheduleSuccess}
        />
      )}
    </div>
  )
}

export default AppointmentHistory
