// Admin page for managing clinic and doctor closures.
//


import { useState, useEffect } from 'react'
import { createClosure, listClosures, deleteClosure } from '../services/closureApi'

// Formats ISO datetime string into something readable"
function formatDate(iso) {
  return new Date(iso).toLocaleString(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short',
  })
}

const EMPTY_FORM = {
  closure_type:   'clinic',
  doctor_id:      '',
  start_datetime: '',
  end_datetime:   '',
  description:    '',
}

export default function ClosuresAdmin() {
  const [closures,    setClosures]    = useState([])
  const [loading,     setLoading]     = useState(true)
  const [form,        setForm]        = useState(EMPTY_FORM)
  const [submitting,  setSubmitting]  = useState(false)
  const [errorMsg,    setErrorMsg]    = useState(null)
  const [successMsg,  setSuccessMsg]  = useState(null)

  useEffect(() => {
    listClosures()
      .then(data => setClosures(data))
      .catch(() => setErrorMsg('Failed to load closures.'))
      .finally(() => setLoading(false))
  }, [])

  function handleChange(e) {
    const { name, value } = e.target
    setForm(prev => ({ ...prev, [name]: value }))
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setErrorMsg(null)
    setSuccessMsg(null)
    setSubmitting(true)

    const payload = {
      closure_type:   form.closure_type,
      start_datetime: form.start_datetime,
      end_datetime:   form.end_datetime,
      description:    form.description || undefined,
    }

    if (form.closure_type === 'doctor') {
      payload.doctor_id = parseInt(form.doctor_id, 10)
    }

    try {
      const newClosure = await createClosure(payload)
      setClosures(prev => [...prev, newClosure])
      setSuccessMsg('Closure created successfully.')
      setForm(EMPTY_FORM)
    } catch (err) {
      setErrorMsg(err.message)
    } finally {
      setSubmitting(false)
    }
  }

  async function handleDelete(id) {
    if (!window.confirm('Are you sure you want to delete this closure?')) return
    try {
      await deleteClosure(id)
      setClosures(prev => prev.filter(c => c.id !== id))
    } catch (err) {
      setErrorMsg('Failed to delete closure: ' + err.message)
    }
  }

  return (
    <div style={styles.page}>
      <h1 style={styles.heading}>Closure Management</h1>
      <p style={styles.subtitle}>
        Define periods when the clinic or a specific doctor is unavailable.
        Appointments cannot be scheduled during these periods.
      </p>

      <section style={styles.card}>
        <h2 style={styles.cardTitle}>New Closure</h2>

        {errorMsg   && <p style={styles.error}>{errorMsg}</p>}
        {successMsg && <p style={styles.success}>{successMsg}</p>}

        <form onSubmit={handleSubmit} style={styles.form}>

          <label style={styles.label}>
            Closure Type
            <select
              name="closure_type"
              value={form.closure_type}
              onChange={handleChange}
              style={styles.input}
            >
              <option value="clinic">Clinic-wide</option>
              <option value="doctor">Doctor-specific</option>
            </select>
          </label>

          {form.closure_type === 'doctor' && (
            <label style={styles.label}>
              Doctor ID
              <input
                type="number"
                name="doctor_id"
                value={form.doctor_id}
                onChange={handleChange}
                min="1"
                required
                placeholder="e.g. 67"
                style={styles.input}
              />
            </label>
          )}

          <label style={styles.label}>
            Start Date &amp; Time
            <input
              type="datetime-local"
              name="start_datetime"
              value={form.start_datetime}
              onChange={handleChange}
              required
              style={styles.input}
            />
          </label>

          <label style={styles.label}>
            End Date &amp; Time
            <input
              type="datetime-local"
              name="end_datetime"
              value={form.end_datetime}
              onChange={handleChange}
              required
              style={styles.input}
            />
          </label>

          <label style={styles.label}>
            Reason <span style={styles.optional}>(optional)</span>
            <input
              type="text"
              name="description"
              value={form.description}
              onChange={handleChange}
              maxLength={255}
              placeholder="Insert reason here"
              style={styles.input}
            />
          </label>

          <button type="submit" disabled={submitting} style={styles.btn}>
            {submitting ? 'Saving…' : 'Create Closure'}
          </button>

        </form>
      </section>

      <section style={styles.card}>
        <h2 style={styles.cardTitle}>Existing Closures</h2>

        {loading ? (
          <p style={styles.muted}>Loading…</p>
        ) : closures.length === 0 ? (
          <p style={styles.muted}>No closures have been added yet.</p>
        ) : (
          <table style={styles.table}>
            <thead>
              <tr>
                <th style={styles.th}>Type</th>
                <th style={styles.th}>Doctor ID</th>
                <th style={styles.th}>Start</th>
                <th style={styles.th}>End</th>
                <th style={styles.th}>Reason</th>
                <th style={styles.th}></th>
              </tr>
            </thead>
            <tbody>
              {closures.map(c => (
                <tr key={c.id} style={styles.tr}>
                  <td style={styles.td}>
                    <span style={c.closure_type === 'clinic' ? styles.badgeClinic : styles.badgeDoctor}>
                      {c.closure_type === 'clinic' ? 'Clinic-wide' : 'Doctor-specific'}
                    </span>
                  </td>
                  <td style={styles.td}>{c.doctor_id ?? '—'}</td>
                  <td style={styles.td}>{formatDate(c.start_datetime)}</td>
                  <td style={styles.td}>{formatDate(c.end_datetime)}</td>
                  <td style={styles.td}>{c.description || '—'}</td>
                  <td style={styles.td}>
                    <button onClick={() => handleDelete(c.id)} style={styles.deleteBtn}>
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </div>
  )
}

// ── Styles ────────────────────────────────────────────────────────────────────

const styles = {
  page:      { maxWidth: 860, margin: '0 auto', padding: '2rem 1rem', fontFamily: 'system-ui, sans-serif', color: '#1a202c' },
  heading:   { fontSize: '1.75rem', fontWeight: 700, marginBottom: '0.25rem' },
  subtitle:  { color: '#4a5568', marginBottom: '2rem' },
  card:      { background: '#fff', border: '1px solid #e2e8f0', borderRadius: 8, padding: '1.5rem', marginBottom: '1.5rem' },
  cardTitle: { fontSize: '1.1rem', fontWeight: 600, marginTop: 0, marginBottom: '1rem' },
  form:      { display: 'flex', flexDirection: 'column', gap: '1rem' },
  label:     { display: 'flex', flexDirection: 'column', gap: '0.25rem', fontSize: '0.875rem', fontWeight: 500 },
  input:     { padding: '0.5rem 0.75rem', border: '1px solid #cbd5e0', borderRadius: 6, fontSize: '0.9rem' },
  optional:  { fontWeight: 400, color: '#718096', marginLeft: 4 },
  btn:       { padding: '0.6rem 1.25rem', background: '#3182ce', color: '#fff', border: 'none', borderRadius: 6, fontWeight: 600, cursor: 'pointer', alignSelf: 'flex-start' },
  error:     { color: '#c53030', background: '#fff5f5', border: '1px solid #feb2b2', borderRadius: 6, padding: '0.5rem 0.75rem' },
  success:   { color: '#276749', background: '#f0fff4', border: '1px solid #9ae6b4', borderRadius: 6, padding: '0.5rem 0.75rem' },
  table:     { width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem' },
  th:        { textAlign: 'left', padding: '0.5rem 0.75rem', borderBottom: '2px solid #e2e8f0', fontWeight: 600, color: '#4a5568' },
  tr:        { borderBottom: '1px solid #edf2f7' },
  td:        { padding: '0.6rem 0.75rem', verticalAlign: 'middle' },
  muted:     { color: '#718096', fontStyle: 'italic' },
  badgeClinic:  { display: 'inline-block', padding: '0.15rem 0.5rem', background: '#ebf8ff', color: '#2b6cb0', borderRadius: 12, fontSize: '0.75rem', fontWeight: 600 },
  badgeDoctor:  { display: 'inline-block', padding: '0.15rem 0.5rem', background: '#faf5ff', color: '#6b46c1', borderRadius: 12, fontSize: '0.75rem', fontWeight: 600 },
  deleteBtn: { padding: '0.25rem 0.6rem', background: 'transparent', color: '#e53e3e', border: '1px solid #feb2b2', borderRadius: 4, cursor: 'pointer', fontSize: '0.8rem' },
}