import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import DoctorProfile from '../pages/DoctorProfile'
import { getProfile, updateProfile } from '../services/api'

//Testing editable fields in DoctorProfile, including ensuring only allowed fields are sent on update and that maxLength is enforced. Also tests that phone number is displayed in formatted form when not editing.

vi.mock('../lib/supabaseClient', () => ({
  supabase: {
    auth: {
      getSession: vi.fn().mockResolvedValue({
        data: { session: { user: { id: 'doctor-uuid-1' } } },
      }),
      signOut: vi.fn(),
    },
    from: vi.fn().mockReturnValue({
      select: vi.fn().mockReturnThis(),
      eq: vi.fn().mockResolvedValue({
        data: [{ roles: { name: 'doctor' } }],
      }),
    }),
  },
}))

vi.mock('../services/api', () => ({
  getProfile: vi.fn(),
  updateProfile: vi.fn(),
}))

const MOCK_PROFILE = {
  user_id: 'doctor-uuid-1',
  first_name: 'Ana',
  last_name: 'Torres',
  display_name: 'Ana Torres',
  username: 'anatorres',
  phone_number: '7871234567',
  specialty: 'Cardiology',
  bio: 'Experienced cardiologist.',
  profession_title: 'MD',
  license_number: 'PR-12345',
  license_state: 'PR',
}

function renderProfile() {
  sessionStorage.setItem('userRole', 'doctor')
  return render(
    <MemoryRouter>
      <DoctorProfile />
    </MemoryRouter>
  )
}

describe('DoctorProfile — editable fields', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    sessionStorage.clear()
    getProfile.mockResolvedValue(MOCK_PROFILE)
    updateProfile.mockResolvedValue(MOCK_PROFILE)
  })

  it('shows Edit Profile button when not editing', async () => {
    renderProfile()
    expect(await screen.findByRole('button', { name: /edit profile/i })).toBeInTheDocument()
  })

  it('only shows editable inputs for phone_number, specialty, and bio when editing', async () => {
    renderProfile()

    fireEvent.click(await screen.findByRole('button', { name: /edit profile/i }))

    // editable fields
    expect(screen.getByDisplayValue('7871234567')).toBeInTheDocument() // phone raw value
    expect(screen.getByDisplayValue('Cardiology')).toBeInTheDocument()
    expect(screen.getByDisplayValue('Experienced cardiologist.')).toBeInTheDocument()

    // Read-only field
    const inputs = screen.getAllByRole('textbox')
    const inputValues = inputs.map(i => i.value)
    expect(inputValues).not.toContain('MD')     
    expect(inputValues).not.toContain('PR-12345') 
    expect(inputValues).not.toContain('PR')      
  })

  it('only sends changed fields from the allowed set when saving', async () => {
    renderProfile()

    fireEvent.click(await screen.findByRole('button', { name: /edit profile/i }))

    const specialtyInput = screen.getByDisplayValue('Cardiology')
    fireEvent.change(specialtyInput, { target: { value: 'Neurology' } })

    fireEvent.click(screen.getByRole('button', { name: /save changes/i }))

    await waitFor(() => {
      expect(updateProfile).toHaveBeenCalledWith('doctor-uuid-1', { specialty: 'Neurology' })
    })

    // Must not send read-only fields
    const callArg = updateProfile.mock.calls[0][1]
    expect(callArg).not.toHaveProperty('profession_title')
    expect(callArg).not.toHaveProperty('license_number')
    expect(callArg).not.toHaveProperty('license_state')
  })

  it('enforces maxLength on specialty (100) and bio (1000) inputs', async () => {
    renderProfile()

    fireEvent.click(await screen.findByRole('button', { name: /edit profile/i }))

    const specialtyInput = screen.getByDisplayValue('Cardiology')
    const bioInput = screen.getByDisplayValue('Experienced cardiologist.')

    expect(specialtyInput).toHaveAttribute('maxLength', '100')
    expect(bioInput).toHaveAttribute('maxLength', '1000')
  })

  it('displays phone number in formatted form when not editing', async () => {
    renderProfile()
    expect(await screen.findByText('(787) 123-4567')).toBeInTheDocument()
  })
})
