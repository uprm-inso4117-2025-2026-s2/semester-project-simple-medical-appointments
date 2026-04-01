import { useEffect, useMemo, useState } from 'react'
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

  const { upcomingAppointments, pastAppointments } = useMemo(() => {
    const normalized = appointments.map((appt) => {
      const dateTime = new Date(
        `${appt.appointment_date} ${appt.appointment_time || '00:00'}`
      )

      return {
        ...appt,
        appointmentDateTime: dateTime,
      }
    })

    return {
      upcomingAppointments: normalized.filter(
        (appt) => appt.status === 'Upcoming' || appt.appointmentDateTime >= new Date()
      ),
      pastAppointments: normalized.filter(
        (appt) => !(appt.status === 'Upcoming' || appt.appointmentDateTime >= new Date())
      ),
    }
  }, [appointments])

  const handleDetails = (appt) => {
    alert(
      `Doctor: ${appt.doctor_name || appt.doctor_id}\nSpecialty: ${
        appt.specialty || appt.status
      }\nDate: ${appt.appointment_date}\nTime: ${appt.appointment_time}\nClinic: ${
        appt.clinic_name || appt.clinic_id
      }\nStatus: ${appt.status}`
    )
  }

  const renderAppointmentCard = (appt) => (
    <div key={appt.id} style={styles.card}>
      <div style={styles.cardIconBox}>
        <span style={styles.cardIcon}>📅</span>
      </div>

      <div style={styles.cardContent}>
        <h3 style={styles.doctorName}>{appt.doctor_name || appt.doctor_id || 'Doctor'}</h3>
        <p style={styles.specialtyText}>{appt.specialty || 'Medical Appointment'}</p>
        <p style={styles.metaText}>
          {appt.appointment_date} • {appt.appointment_time}
        </p>
        <p style={styles.metaText}>{appt.clinic_name || appt.clinic_id}</p>

        <div style={styles.cardFooterRow}>
          <span
            style={{
              ...styles.statusBadge,
              ...(appt.status === 'Upcoming'
                ? styles.upcomingBadge
                : appt.status === 'Cancelled'
                ? styles.cancelledBadge
                : styles.completedBadge),
            }}
          >
            {appt.status}
          </span>

          <button style={styles.detailsButton} onClick={() => handleDetails(appt)}>
            Appointment Details
          </button>
        </div>
      </div>
    </div>
  )

  if (loading) {
    return <div style={styles.stateMessage}>Loading appointment history…</div>
  }

  if (error) {
    return <div style={{ ...styles.stateMessage, color: '#ffb4b4' }}>Error: {error}</div>
  }

  return (
    <div style={styles.page}>
      <header style={styles.topbar}>
        <div style={styles.brand}>
          <div style={styles.brandIcon}>⚕️</div>
          <span style={styles.brandText}>Simple Medical Appointments</span>
        </div>

        <div style={styles.topbarRight}>
          <span style={styles.emailText}>pedro.morales38@upr.edu</span>
          <button style={styles.logoutButton}>Log out</button>
        </div>
      </header>

      <main style={styles.main}>
        <div style={styles.hero}>
          <p style={styles.eyebrow}>Appointment history</p>
          <h1 style={styles.title}>My Appointments</h1>
          <p style={styles.subtitle}>View your full appointment history and upcoming visits.</p>
        </div>

        <section style={styles.section}>
          <h2 style={styles.sectionTitle}>Upcoming Appointments</h2>
          <div style={styles.cardsWrapper}>
            {upcomingAppointments.length > 0 ? (
              upcomingAppointments.map(renderAppointmentCard)
            ) : (
              <p style={styles.emptyText}>No upcoming appointments.</p>
            )}
          </div>
        </section>

        <section style={styles.section}>
          <h2 style={styles.sectionTitle}>Appointment History</h2>
          <div style={styles.cardsWrapper}>
            {pastAppointments.length > 0 ? (
              pastAppointments.map(renderAppointmentCard)
            ) : (
              <p style={styles.emptyText}>No appointment history found.</p>
            )}
          </div>
        </section>
      </main>
    </div>
  )
}

const styles = {
  page: {
    minHeight: '100vh',
    fontFamily:
      'Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
    background:
      'radial-gradient(circle at top, #082c3a 0%, #041821 45%, #021118 100%)',
    color: '#f5f7fa',
  },
  topbar: {
    height: '86px',
    borderBottom: '1px solid rgba(255,255,255,0.08)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '0 48px',
    backgroundColor: 'rgba(0,0,0,0.08)',
    backdropFilter: 'blur(4px)',
  },
  brand: {
    display: 'flex',
    alignItems: 'center',
    gap: '14px',
  },
  brandIcon: {
    width: '40px',
    height: '40px',
    borderRadius: '12px',
    background: '#0c3f52',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: '20px',
  },
  brandText: {
    fontSize: '18px',
    fontWeight: 700,
    color: '#ffffff',
  },
  topbarRight: {
    display: 'flex',
    alignItems: 'center',
    gap: '18px',
  },
  emailText: {
    color: 'rgba(255,255,255,0.82)',
    fontSize: '16px',
  },
  logoutButton: {
    border: '1px solid rgba(255,255,255,0.18)',
    background: 'rgba(255,255,255,0.08)',
    color: '#fff',
    borderRadius: '999px',
    padding: '12px 22px',
    fontSize: '16px',
    cursor: 'pointer',
  },
  main: {
    maxWidth: '1180px',
    margin: '0 auto',
    padding: '56px 28px 80px',
  },
  hero: {
    textAlign: 'center',
    marginBottom: '48px',
  },
  eyebrow: {
    margin: 0,
    color: '#88b8c7',
    fontSize: '16px',
    textTransform: 'uppercase',
    letterSpacing: '0.08em',
  },
  title: {
    margin: '12px 0 12px',
    fontSize: '64px',
    lineHeight: 1,
    fontWeight: 800,
    color: '#ffffff',
  },
  subtitle: {
    margin: 0,
    fontSize: '22px',
    color: 'rgba(255,255,255,0.72)',
  },
  section: {
    marginBottom: '42px',
  },
  sectionTitle: {
    fontSize: '30px',
    fontWeight: 700,
    marginBottom: '18px',
    color: '#ffffff',
  },
  cardsWrapper: {
    display: 'grid',
    gap: '22px',
  },
  card: {
    background: '#f5f7fa',
    color: '#13202b',
    borderRadius: '28px',
    padding: '26px',
    display: 'flex',
    gap: '20px',
    boxShadow: '0 14px 30px rgba(0,0,0,0.18)',
  },
  cardIconBox: {
    width: '74px',
    height: '74px',
    borderRadius: '20px',
    background: '#0f5e79',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0,
  },
  cardIcon: {
    fontSize: '28px',
  },
  cardContent: {
    flex: 1,
  },
  doctorName: {
    margin: '0 0 8px 0',
    fontSize: '30px',
    fontWeight: 800,
    color: '#162333',
  },
  specialtyText: {
    margin: '0 0 8px 0',
    fontSize: '19px',
    color: '#40515f',
  },
  metaText: {
    margin: '0 0 6px 0',
    fontSize: '16px',
    color: '#5f6d79',
  },
  cardFooterRow: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    gap: '16px',
    marginTop: '18px',
    flexWrap: 'wrap',
  },
  statusBadge: {
    display: 'inline-flex',
    alignItems: 'center',
    borderRadius: '999px',
    padding: '8px 14px',
    fontSize: '14px',
    fontWeight: 700,
  },
  upcomingBadge: {
    backgroundColor: '#d9f3e4',
    color: '#17653b',
  },
  completedBadge: {
    backgroundColor: '#dceaf9',
    color: '#174a7a',
  },
  cancelledBadge: {
    backgroundColor: '#f8dcdc',
    color: '#8a1f1f',
  },
  detailsButton: {
    border: 'none',
    background: '#0f7ea5',
    color: '#fff',
    borderRadius: '14px',
    padding: '12px 18px',
    fontSize: '15px',
    fontWeight: 700,
    cursor: 'pointer',
  },
  emptyText: {
    color: 'rgba(255,255,255,0.72)',
    fontSize: '16px',
  },
  stateMessage: {
    minHeight: '100vh',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    background:
      'radial-gradient(circle at top, #082c3a 0%, #041821 45%, #021118 100%)',
    color: '#ffffff',
    fontSize: '20px',
    fontFamily:
      'Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
  },
}

export default AppointmentHistory