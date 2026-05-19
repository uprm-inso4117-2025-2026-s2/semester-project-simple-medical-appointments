import { render, screen, within } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import AppointmentHistory from './AppointmentHistory'
import { getAllAppointmentHistory } from '../services/api'

vi.mock('../services/api', () => ({
  getAllAppointmentHistory: vi.fn(),
}))

describe('AppointmentHistory', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('shows a loading message while appointment history is being fetched', () => {
    getAllAppointmentHistory.mockReturnValue(new Promise(() => {}))

    render(<AppointmentHistory />)

    expect(screen.getByText(/loading appointment history/i)).toBeInTheDocument()
    expect(getAllAppointmentHistory).toHaveBeenCalledTimes(1)
  })

  it('shows an error message when the appointment history request fails', async () => {
    getAllAppointmentHistory.mockRejectedValue(new Error('Network failed'))

    render(<AppointmentHistory />)

    expect(
      await screen.findByRole('heading', { name: /unable to load appointment history/i })
    ).toBeInTheDocument()
    expect(screen.getByText(/network failed/i)).toBeInTheDocument()
  })

  it('shows an empty state when no appointments are returned', async () => {
    getAllAppointmentHistory.mockResolvedValue([])

    render(<AppointmentHistory />)

    expect(await screen.findByText(/no appointments found/i)).toBeInTheDocument()
    expect(
      screen.getByText(/once appointments are booked, they will appear here/i)
    ).toBeInTheDocument()
  })

  it('renders the appointment summary and table data when appointments are returned', async () => {
    getAllAppointmentHistory.mockResolvedValue([
      {
        id: 1,
        patient_id: 42,
        doctor_name: 'Dr. Future',
        clinic_name: 'Future Clinic',
        appointment_datetime: '2099-06-15T09:30:00-04:00',
        status: 'confirmed',
      },
      {
        id: 2,
        patient_id: 42,
        doctor_name: 'Dr. Past',
        clinic_name: 'Past Clinic',
        appointment_datetime: '2020-01-10T14:00:00-04:00',
        status: 'completed',
      },
    ])

    render(<AppointmentHistory />)

    expect(await screen.findByText('Dr. Future')).toBeInTheDocument()
    expect(screen.getByText('Dr. Past')).toBeInTheDocument()
    expect(screen.getByText('Future Clinic')).toBeInTheDocument()
    expect(screen.getByText('Past Clinic')).toBeInTheDocument()

    const summarySection = screen.getByLabelText(/appointment summary/i)
    const totalCard = within(summarySection).getByText(/total appointments/i).closest('article')
    const confirmedCard = within(summarySection).getByText(/^confirmed$/i).closest('article')
    const completedCard = within(summarySection).getByText(/^completed$/i).closest('article')

    expect(totalCard).not.toBeNull()
    expect(confirmedCard).not.toBeNull()
    expect(completedCard).not.toBeNull()

    expect(within(totalCard).getByText('2')).toBeInTheDocument()
    expect(within(confirmedCard).getByText('1')).toBeInTheDocument()
    expect(within(completedCard).getByText('1')).toBeInTheDocument()
  })

  it('renders fallback values for missing appointment fields', async () => {
    getAllAppointmentHistory.mockResolvedValue([
      {
        id: 7,
        patient_id: null,
        doctor_name: null,
        clinic_name: null,
        appointment_datetime: null,
        status: null,
      },
    ])

    render(<AppointmentHistory />)

    expect(await screen.findByText('N/A')).toBeInTheDocument()
    expect(screen.getByText('Unassigned')).toBeInTheDocument()
    expect(screen.getByText('Unknown clinic')).toBeInTheDocument()
    expect(screen.getByText('Not scheduled')).toBeInTheDocument()
    expect(screen.getByText('Unknown')).toBeInTheDocument()
  })
})
