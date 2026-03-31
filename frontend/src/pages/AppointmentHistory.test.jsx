import { fireEvent, render, screen, within } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import AppointmentHistory from './AppointmentHistory'
import { getAppointmentHistory } from '../services/api'

vi.mock('../services/api', () => ({
  getAppointmentHistory: vi.fn(),
}))

describe('AppointmentHistory', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  // Test the loading state
  it('shows a loading message while appointment history is being fetched', () => {
    getAppointmentHistory.mockReturnValue(new Promise(() => {}))

    render(<AppointmentHistory />)

    expect(screen.getByText(/loading appointment history/i)).toBeInTheDocument()
    expect(getAppointmentHistory).toHaveBeenCalledWith(1)
  })

  // Test what happens when the appointment history is unsuccessfully fetched
  it('shows an error message when the appointment history request fails', async () => {
    getAppointmentHistory.mockRejectedValue(new Error('Network failed'))

    render(<AppointmentHistory />)
    // wait for the error message to appear
    expect(await screen.findByText(/error: network failed/i)).toBeInTheDocument()
  })

  // Test no past nor upcoming appointments by moking an empty array response from the API
  it('shows empty-state messages when the patient has no appointments', async () => {
    getAppointmentHistory.mockResolvedValue([])

    render(<AppointmentHistory />)

    expect(await screen.findByText(/no upcoming appointments\./i)).toBeInTheDocument()
    expect(screen.getByText(/no appointment history found\./i)).toBeInTheDocument()
  })

  // Test that appointments are correctly separated into upcoming and past sections
  it('separates upcoming and past appointments into the correct sections', async () => {
    // id 1 is an upcoming appointment, id 2 is a past appointment
    getAppointmentHistory.mockResolvedValue([
      {
        id: 1,
        doctor_name: 'Dr. Future',
        specialty: 'Cardiology',
        appointment_date: '2099-06-15',
        appointment_time: '09:30',
        clinic_name: 'Future Clinic',
        status: 'Upcoming',
      },
      {
        id: 2,
        doctor_name: 'Dr. Past',
        specialty: 'Dermatology',
        appointment_date: '2020-01-10',
        appointment_time: '14:00',
        clinic_name: 'Past Clinic',
        status: 'Completed',
      },
    ])

    render(<AppointmentHistory />)

    // find upcoming and history sections by their headings
    const upcomingSection = (await screen.findByRole('heading', {
      name: /upcoming appointments/i,
    })).closest('section')
    const historySection = screen
      .getByRole('heading', { name: /^appointment history$/i, level: 2 })
      .closest('section')

    expect(upcomingSection).not.toBeNull()
    expect(historySection).not.toBeNull()

    // check that the upcoming section contains the upcoming appointment and not the past one
    expect(within(upcomingSection).getByText('Dr. Future')).toBeInTheDocument()
    expect(within(upcomingSection).queryByText('Dr. Past')).not.toBeInTheDocument()

    // check that the history section contains the past appointment and not the upcoming one
    expect(within(historySection).getByText('Dr. Past')).toBeInTheDocument()
    expect(within(historySection).queryByText('Dr. Future')).not.toBeInTheDocument()
  })

  // Test that clicking the details button shows an alert with the correct appointment details
  it('shows appointment details in an alert when the details button is clicked', async () => {
    const alertSpy = vi.spyOn(window, 'alert').mockImplementation(() => {})
    // mock an appointment response from the API
    getAppointmentHistory.mockResolvedValue([
      {
        id: 1,
        doctor_name: 'Dr. Rivera',
        specialty: 'Pediatrics',
        appointment_date: '2099-08-21',
        appointment_time: '11:15',
        clinic_name: 'San Juan Clinic',
        status: 'Upcoming',
      },
    ])

    render(<AppointmentHistory />)

    const detailsButton = await screen.findByRole('button', {
      name: /appointment details/i,
    })

    fireEvent.click(detailsButton)

    // check that the alert was called with a string containing all the relevant appointment details
    expect(alertSpy).toHaveBeenCalledWith(
      expect.stringContaining('Doctor: Dr. Rivera')
    )
    expect(alertSpy).toHaveBeenCalledWith(
      expect.stringContaining('Specialty: Pediatrics')
    )
    expect(alertSpy).toHaveBeenCalledWith(
      expect.stringContaining('Date: 2099-08-21')
    )
    expect(alertSpy).toHaveBeenCalledWith(
      expect.stringContaining('Time: 11:15')
    )
    expect(alertSpy).toHaveBeenCalledWith(
      expect.stringContaining('Clinic: San Juan Clinic')
    )
    expect(alertSpy).toHaveBeenCalledWith(
      expect.stringContaining('Status: Upcoming')
    )
  })
})
