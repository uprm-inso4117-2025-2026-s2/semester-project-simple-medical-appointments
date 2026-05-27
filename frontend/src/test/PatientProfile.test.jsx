import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import PatientProfile from '../pages/PatientProfile'
import { getProfile, updateProfile } from '../services/api'
 
// Tests for the PatientProfile edit / save flow:
//   - entering edit mode reveals the correct editable fields
//   - invalid phone number (too short) blocks save and shows an error
//   - valid save sends only the changed fields and excludes read-only fields
 
vi.mock('../lib/supabaseClient', () => ({
  supabase: {
    auth: {
      getSession: vi.fn().mockResolvedValue({
        data: { session: { user: { id: 'patient-uuid-1' } } },
      }),
      signOut: vi.fn(),
    },
    from: vi.fn().mockReturnValue({
      select: vi.fn().mockReturnThis(),
      eq: vi.fn().mockResolvedValue({
        data: [{ roles: { name: 'patient' } }],
      }),
    }),
  },
}))
 
vi.mock('../services/api', () => ({
  getProfile: vi.fn(),
  updateProfile: vi.fn(),
}))
 
// phone fields are placed into editValues raw (no formatting on edit-start)
const MOCK_PROFILE = {
  user_id: 'patient-uuid-1',
  first_name: 'Maria',
  last_name: 'Colón',
  display_name: 'Maria Colón',
  username: 'mariacolon',
  phone_number: '7875550100',
  insurance_provider: 'BlueCross',
  insurance_member_id: 'BC-99001',
  emergency_contact_name: 'Carlos Colón',
  emergency_contact_phone: '7875550199',
}
 
function renderProfile() {
  sessionStorage.setItem('userRole', 'patient')
  return render(
    <MemoryRouter>
      <PatientProfile />
    </MemoryRouter>
  )
}
 
// ── Edit mode ────────────────────────────────────────────────────────────────
 
describe('PatientProfile — edit mode', () => {
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
 
  it('entering edit mode shows a phone input with the raw stored value', async () => {
    renderProfile()
 
    fireEvent.click(await screen.findByRole('button', { name: /edit profile/i }))
 
    expect(screen.getByDisplayValue('7875550100')).toBeInTheDocument()
  })
 
  it('entering edit mode shows editable inputs for insurance fields', async () => {
    renderProfile()
 
    fireEvent.click(await screen.findByRole('button', { name: /edit profile/i }))
 
    expect(screen.getByDisplayValue('BlueCross')).toBeInTheDocument()
    expect(screen.getByDisplayValue('BC-99001')).toBeInTheDocument()
  })
 
  it('entering edit mode shows editable inputs for emergency contact fields', async () => {
    renderProfile()
 
    fireEvent.click(await screen.findByRole('button', { name: /edit profile/i }))
 
    expect(screen.getByDisplayValue('Carlos Colón')).toBeInTheDocument()
    expect(screen.getByDisplayValue('7875550199')).toBeInTheDocument()
  })
 
  it('read-only fields (first name, last name, display name) are not editable inputs', async () => {
    renderProfile()
 
    fireEvent.click(await screen.findByRole('button', { name: /edit profile/i }))
 
    const inputValues = screen.getAllByRole('textbox').map(i => i.value)
    expect(inputValues).not.toContain('Maria')
    expect(inputValues).not.toContain('Maria Colón')
  })
 
  it('Save Changes and Cancel buttons appear while editing', async () => {
    renderProfile()
 
    fireEvent.click(await screen.findByRole('button', { name: /edit profile/i }))
 
    expect(screen.getByRole('button', { name: /save changes/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument()
  })
})
 
// ── Phone validation ──────────────────────────────────────────────────────────
 
describe('PatientProfile — phone validation', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    sessionStorage.clear()
    getProfile.mockResolvedValue(MOCK_PROFILE)
    updateProfile.mockResolvedValue(MOCK_PROFILE)
  })
 
  it('blocks save and shows an error when phone number has fewer than 10 digits', async () => {
    renderProfile()
 
    fireEvent.click(await screen.findByRole('button', { name: /edit profile/i }))
 
    const phoneInput = screen.getByDisplayValue('7875550100')
    fireEvent.change(phoneInput, { target: { value: '787' } })
 
    fireEvent.click(screen.getByRole('button', { name: /save changes/i }))
 
    await waitFor(() => {
      expect(screen.getByText(/valid 10-digit number/i)).toBeInTheDocument()
    })
 
    expect(updateProfile).not.toHaveBeenCalled()
  })
 
  it('blocks save and shows an error when emergency contact phone has fewer than 10 digits', async () => {
    renderProfile()
 
    fireEvent.click(await screen.findByRole('button', { name: /edit profile/i }))
 
    const ecPhoneInput = screen.getByDisplayValue('7875550199')
    fireEvent.change(ecPhoneInput, { target: { value: '555' } })
 
    fireEvent.click(screen.getByRole('button', { name: /save changes/i }))
 
    await waitFor(() => {
      expect(screen.getByText(/valid 10-digit number/i)).toBeInTheDocument()
    })
 
    expect(updateProfile).not.toHaveBeenCalled()
  })
})
 
// ── Valid save ────────────────────────────────────────────────────────────────
 
describe('PatientProfile — valid save', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    sessionStorage.clear()
    getProfile.mockResolvedValue(MOCK_PROFILE)
    updateProfile.mockResolvedValue(MOCK_PROFILE)
  })
 
  it('sends only the changed phone field and excludes read-only fields', async () => {
    renderProfile()
 
    fireEvent.click(await screen.findByRole('button', { name: /edit profile/i }))
 
    const phoneInput = screen.getByDisplayValue('7875550100')
    fireEvent.change(phoneInput, { target: { value: '7875559999' } })
 
    fireEvent.click(screen.getByRole('button', { name: /save changes/i }))
 
    await waitFor(() => {
      expect(updateProfile).toHaveBeenCalledWith(
        'patient-uuid-1',
        expect.objectContaining({ phone_number: '(787) 555-9999' })
      )
    })
 
    const callArg = updateProfile.mock.calls[0][1]
    expect(callArg).not.toHaveProperty('first_name')
    expect(callArg).not.toHaveProperty('last_name')
    expect(callArg).not.toHaveProperty('display_name')
    expect(callArg).not.toHaveProperty('username')
  })
 
  it('sends only the changed insurance fields', async () => {
    renderProfile()
 
    fireEvent.click(await screen.findByRole('button', { name: /edit profile/i }))
 
    const providerInput = screen.getByDisplayValue('BlueCross')
    fireEvent.change(providerInput, { target: { value: 'Aetna' } })
 
    const memberIdInput = screen.getByDisplayValue('BC-99001')
    fireEvent.change(memberIdInput, { target: { value: 'AE-12345' } })
 
    fireEvent.click(screen.getByRole('button', { name: /save changes/i }))
 
    await waitFor(() => {
      expect(updateProfile).toHaveBeenCalledWith('patient-uuid-1', {
        insurance_provider: 'Aetna',
        insurance_member_id: 'AE-12345',
      })
    })
 
    const callArg = updateProfile.mock.calls[0][1]
    expect(callArg).not.toHaveProperty('phone_number')
    expect(callArg).not.toHaveProperty('first_name')
  })
 
  it('sends only the changed emergency contact name field', async () => {
    renderProfile()
 
    fireEvent.click(await screen.findByRole('button', { name: /edit profile/i }))
 
    const contactNameInput = screen.getByDisplayValue('Carlos Colón')
    fireEvent.change(contactNameInput, { target: { value: 'Ana Rivera' } })
 
    fireEvent.click(screen.getByRole('button', { name: /save changes/i }))
 
    await waitFor(() => {
      expect(updateProfile).toHaveBeenCalledWith('patient-uuid-1', {
        emergency_contact_name: 'Ana Rivera',
      })
    })
 
    const callArg = updateProfile.mock.calls[0][1]
    expect(callArg).not.toHaveProperty('insurance_provider')
    expect(callArg).not.toHaveProperty('first_name')
  })
 
  it('does not call updateProfile when no fields have changed', async () => {
    renderProfile()
 
    fireEvent.click(await screen.findByRole('button', { name: /edit profile/i }))
 
    fireEvent.click(screen.getByRole('button', { name: /save changes/i }))
 
    await waitFor(() => {
      expect(updateProfile).not.toHaveBeenCalled()
    })
  })
 
  it('shows a save-error message when updateProfile rejects', async () => {
    updateProfile.mockRejectedValueOnce(new Error('Network error'))
 
    renderProfile()
 
    fireEvent.click(await screen.findByRole('button', { name: /edit profile/i }))
 
    const providerInput = screen.getByDisplayValue('BlueCross')
    fireEvent.change(providerInput, { target: { value: 'Aetna' } })
 
    fireEvent.click(screen.getByRole('button', { name: /save changes/i }))
 
    await screen.findByText(/failed to save/i)
  })
})