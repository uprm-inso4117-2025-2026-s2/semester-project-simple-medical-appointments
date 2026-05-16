import { useState, useEffect, useCallback } from 'react'
import { getAppointments, cancelAppointment } from '../services/api'

// Status badge colours
const STATUS_STYLES = {
  ACTIVE:    { bg: '#dbeafe', color: '#1e40af', label: 'Active' },
  CONFIRMED: { bg: '#dcfce7', color: '#166534', label: 'Confirmed' },
  CANCELLED: { bg: '#fee2e2', color: '#991b1b', label: 'Cancelled' },
  COMPLETED: { bg: '#f3f4f6', color: '#374151', label: 'Completed' },
  NO_SHOW:   { bg: '#fef3c7', color: '#92400e', label: 'No-Show' },
}

const ALL_STATUSES = ['', 'ACTIVE', 'CONFIRMED', 'CANCELLED', 'COMPLETED', 'NO_SHOW']

function StatusBadge({ status }) {
  const style = STATUS_STYLES[status] || { bg: '#f3f4f6', color: '#374151', label: status }
  return (
    <span style={{
      backgroundColor: style.bg,
      color: style.color,
      padding: '2px 10px',
      borderRadius: '9999px',
      fontSize: '0.75rem',
      fontWeight: 600,
      whiteSpace: 'nowrap',
    }}>
      {style.label}
    </span>
  )
}

// ---------------------------------------------------------------------------
// Cancel Modal
// ---------------------------------------------------------------------------
function CancelModal({ appointment, onConfirm, onClose, loading }) {
  const [reason, setReason] = useState('')

  function handleSubmit(e) {
    e.preventDefault()
    onConfirm(appointment.id, reason)
  }

  return (
    <div style={{
      position: 'fixed', inset: 0,
      backgroundColor: 'rgba(0,0,0,0.45)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      zIndex: 50,
    }}>
      <div style={{
        background: '#fff', borderRadius: 12, padding: 32,
        width: '100%', maxWidth: 440, boxShadow: '0 20px 60px rgba(0,0,0,0.2)',
      }}>
        <h2 style={{ margin: '0 0 8px', fontSize: '1.15rem', fontWeight: 700, color: '#111' }}>
          Cancel Appointment
        </h2>
        <p style={{ margin: '0 0 20px', fontSize: '0.875rem', color: '#6b7280' }}>
          Appointment <strong>#{appointment.id}</strong> — {appointment.patient_name} with {appointment.provider_name}
        </p>

        <form onSubmit={handleSubmit}>
          <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: 600, marginBottom: 6, color: '#374151' }}>
            Cancellation reason <span style={{ color: '#9ca3af', fontWeight: 400 }}>(optional)</span>
          </label>
          <textarea
            value={reason}
            onChange={e => setReason(e.target.value)}
            placeholder="e.g. Doctor unavailable, patient request…"
            rows={3}
            disabled={loading}
            style={{
              width: '100%', padding: '8px 12px',
              border: '1px solid #d1d5db', borderRadius: 8,
              fontSize: '0.875rem', resize: 'vertical',
              fontFamily: 'inherit', boxSizing: 'border-box',
              outline: 'none',
            }}
          />

          <div style={{ display: 'flex', gap: 10, marginTop: 20, justifyContent: 'flex-end' }}>
            <button
              type="button"
              onClick={onClose}
              disabled={loading}
              style={{
                padding: '8px 18px', borderRadius: 8, border: '1px solid #d1d5db',
                background: '#fff', cursor: 'pointer', fontSize: '0.875rem', fontWeight: 600,
              }}
            >
              Keep Appointment
            </button>
            <button
              type="submit"
              disabled={loading}
              style={{
                padding: '8px 18px', borderRadius: 8, border: 'none',
                background: loading ? '#fca5a5' : '#dc2626',
                color: '#fff', cursor: loading ? 'not-allowed' : 'pointer',
                fontSize: '0.875rem', fontWeight: 600,
              }}
            >
              {loading ? 'Cancelling…' : 'Confirm Cancellation'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------
export default function AdminAppointments() {
  const [appointments, setAppointments] = useState([])
  const [statusFilter, setStatusFilter] = useState('')
  const [pageLoading, setPageLoading] = useState(true)
  const [pageError, setPageError] = useState(null)

  const [selected, setSelected] = useState(null)   // appointment to cancel
  const [cancelLoading, setCancelLoading] = useState(false)
  const [toast, setToast] = useState(null)          // { type, message }

  // Fetch appointments whenever filter changes
  const fetchAppointments = useCallback(async () => {
    setPageLoading(true)
    setPageError(null)
    try {
      const data = await getAppointments(statusFilter)
      setAppointments(data)
    } catch (err) {
      setPageError(err.message)
    } finally {
      setPageLoading(false)
    }
  }, [statusFilter])

  useEffect(() => { fetchAppointments() }, [fetchAppointments])

  function showToast(type, message) {
    setToast({ type, message })
    setTimeout(() => setToast(null), 4000)
  }

  async function handleCancelConfirm(id, reason) {
    setCancelLoading(true)
    try {
      await cancelAppointment(id, reason, /* cancelledById */ null)
      setSelected(null)
      showToast('success', `Appointment #${id} has been cancelled. The time slot is now available.`)
      fetchAppointments()
    } catch (err) {
      showToast('error', err.message)
    } finally {
      setCancelLoading(false)
    }
  }

  const canCancel = (status) => status === 'ACTIVE' || status === 'CONFIRMED'

  return (
    <div style={{ fontFamily: 'system-ui, sans-serif', padding: '32px 24px', maxWidth: 1100, margin: '0 auto' }}>

      {/* Header */}
      <div style={{ marginBottom: 28 }}>
        <h1 style={{ fontSize: '1.5rem', fontWeight: 700, margin: 0, color: '#111' }}>
          Appointments
        </h1>
        <p style={{ margin: '4px 0 0', color: '#6b7280', fontSize: '0.9rem' }}>
          Manage and cancel scheduled appointments. Cancelling a slot makes it available again for new bookings.
        </p>
      </div>

      {/* Filters */}
      <div style={{ display: 'flex', gap: 12, alignItems: 'center', marginBottom: 24, flexWrap: 'wrap' }}>
        <label style={{ fontSize: '0.875rem', fontWeight: 600, color: '#374151' }}>Filter by status:</label>
        <select
          value={statusFilter}
          onChange={e => setStatusFilter(e.target.value)}
          style={{
            padding: '6px 12px', borderRadius: 8, border: '1px solid #d1d5db',
            fontSize: '0.875rem', background: '#fff', cursor: 'pointer',
          }}
        >
          {ALL_STATUSES.map(s => (
            <option key={s} value={s}>{s === '' ? 'All statuses' : s}</option>
          ))}
        </select>

        <button
          onClick={fetchAppointments}
          style={{
            marginLeft: 'auto', padding: '6px 14px', borderRadius: 8,
            border: '1px solid #d1d5db', background: '#fff',
            fontSize: '0.875rem', cursor: 'pointer', fontWeight: 600,
          }}
        >
          ↺ Refresh
        </button>
      </div>

      {/* Toast */}
      {toast && (
        <div style={{
          padding: '12px 18px', borderRadius: 8, marginBottom: 20,
          background: toast.type === 'success' ? '#dcfce7' : '#fee2e2',
          color: toast.type === 'success' ? '#166534' : '#991b1b',
          fontSize: '0.875rem', fontWeight: 500,
          border: `1px solid ${toast.type === 'success' ? '#bbf7d0' : '#fecaca'}`,
        }}>
          {toast.message}
        </div>
      )}

      {/* Table */}
      {pageLoading ? (
        <div style={{ textAlign: 'center', padding: '60px 0', color: '#9ca3af' }}>Loading appointments…</div>
      ) : pageError ? (
        <div style={{
          padding: '16px', borderRadius: 8, background: '#fee2e2',
          color: '#991b1b', fontSize: '0.875rem',
        }}>
          Failed to load appointments: {pageError}
        </div>
      ) : appointments.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '60px 0', color: '#9ca3af' }}>
          No appointments found{statusFilter ? ` with status "${statusFilter}"` : ''}.
        </div>
      ) : (
        <div style={{ overflowX: 'auto', borderRadius: 10, border: '1px solid #e5e7eb' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem' }}>
            <thead>
              <tr style={{ background: '#f9fafb', borderBottom: '1px solid #e5e7eb' }}>
                {['ID', 'Patient', 'Provider', 'Date & Time', 'Status', 'Cancellation Reason', 'Actions'].map(h => (
                  <th key={h} style={{
                    padding: '10px 16px', textAlign: 'left',
                    fontWeight: 600, color: '#374151', whiteSpace: 'nowrap',
                  }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {appointments.map((appt, i) => {
                const slot = appt.time_slot
                const dateStr = slot
                  ? new Date(slot.start_time).toLocaleString(undefined, {
                      dateStyle: 'medium', timeStyle: 'short',
                    })
                  : '—'
                const cancellable = canCancel(appt.status)

                return (
                  <tr
                    key={appt.id}
                    style={{
                      borderBottom: i < appointments.length - 1 ? '1px solid #f3f4f6' : 'none',
                      background: i % 2 === 0 ? '#fff' : '#fafafa',
                    }}
                  >
                    <td style={{ padding: '12px 16px', color: '#6b7280' }}>#{appt.id}</td>
                    <td style={{ padding: '12px 16px', fontWeight: 500 }}>{appt.patient_name || '—'}</td>
                    <td style={{ padding: '12px 16px' }}>{appt.provider_name || '—'}</td>
                    <td style={{ padding: '12px 16px', whiteSpace: 'nowrap' }}>{dateStr}</td>
                    <td style={{ padding: '12px 16px' }}>
                      <StatusBadge status={appt.status} />
                    </td>
                    <td style={{ padding: '12px 16px', color: '#6b7280', maxWidth: 220 }}>
                      {appt.cancellation_reason
                        ? <span title={appt.cancellation_reason} style={{ cursor: 'help' }}>
                            {appt.cancellation_reason.length > 50
                              ? appt.cancellation_reason.slice(0, 50) + '…'
                              : appt.cancellation_reason}
                          </span>
                        : <span style={{ color: '#d1d5db' }}>—</span>
                      }
                    </td>
                    <td style={{ padding: '12px 16px' }}>
                      {cancellable ? (
                        <button
                          onClick={() => setSelected(appt)}
                          style={{
                            padding: '5px 12px', borderRadius: 6,
                            border: '1px solid #fca5a5',
                            background: '#fff5f5', color: '#dc2626',
                            cursor: 'pointer', fontSize: '0.8rem', fontWeight: 600,
                          }}
                        >
                          Cancel
                        </button>
                      ) : (
                        <span style={{ color: '#d1d5db', fontSize: '0.8rem' }}>—</span>
                      )}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* Cancel modal */}
      {selected && (
        <CancelModal
          appointment={selected}
          onConfirm={handleCancelConfirm}
          onClose={() => setSelected(null)}
          loading={cancelLoading}
        />
      )}
    </div>
  )
}
