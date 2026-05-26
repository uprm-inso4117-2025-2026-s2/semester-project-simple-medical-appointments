import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { login, getSession, onAuthStateChange } from '../services/authService'
import Login from '../pages/Login'

/**
 * These tests validate the full login flow — from credentials submission
 * to session retrieval and role resolution.
 * We are testing both the authService layer and the Login component, including:
 *
 * <-------- authService: getSession() -------->
 * - Returns { user, session, role } when a valid session exists
 * - Returns null when no session exists
 * - Returns null role if user has no role assigned
 *
 * <-------- authService: login() edge cases -------->
 * - Unverified email returns the correct user-facing error
 * - Unknown error falls back to raw message
 *
 * <-------- authService: onAuthStateChange() -------->
 * - Calls back with { user, session, role } on login event
 * - Calls back with null on logout event
 *
 * <-------- Login component -------->
 * - Renders email and password fields
 * - Calls supabase.auth.signInWithPassword with correct credentials
 * - Navigates to '/' on successful login
 * - Shows error message on wrong credentials
 * - Shows error message on unverified email
 * - Button shows loading state while request is in flight
 *
 * <-------- MOCKING STRATEGY -------->
 * - Supabase is fully mocked via vi.mock()
 * - useNavigate is mocked to capture redirect calls
 * - No real network or database calls are made
 *
 * <-------- NOTE ON ROLE-BASED REDIRECTS -------->
 * Role-based redirects (/patient-dashboard, /doctor-dashboard, /admin-dashboard)
 * are not yet implemented in the frontend (Home.jsx does not exist).
 * Once Home.jsx is built with redirect logic based on session role, add tests here:
 *
 *   it('redirects patient to /patient-dashboard', ...)
 *   it('redirects doctor to /doctor-dashboard', ...)
 *   it('redirects admin to /admin-dashboard', ...)
 *
 * For testing go to frontend directory in terminal: cd frontend
 * Run the test file with: npx vitest run src/test/login.test.jsx
 */


// ─────────────────────────────────────────────────────────────────────────────
// SUPABASE MOCK
// ─────────────────────────────────────────────────────────────────────────────

vi.mock('../lib/supabaseClient', () => ({
  supabase: {
    auth: {
      signInWithPassword: vi.fn(),
      getSession: vi.fn(),
      signOut: vi.fn(),
      onAuthStateChange: vi.fn(),
    },
    from: vi.fn(),
  },
}))

// ─────────────────────────────────────────────────────────────────────────────
// REACT ROUTER MOCK
// ─────────────────────────────────────────────────────────────────────────────

const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  }
})

import { supabase } from '../lib/supabaseClient'


// ─────────────────────────────────────────────────────────────────────────────
// authService — getSession()
// ─────────────────────────────────────────────────────────────────────────────

describe('authService - getSession', () => {
  beforeEach(() => vi.clearAllMocks())

  //<------------------- SUCCESS: SESSION WITH ROLE ─────────────────────────>
  it('returns user, session and role when a valid session exists', async () => {
    supabase.auth.getSession.mockResolvedValue({
      data: {
        session: {
          user: { id: 'user-1', email: 'test@test.com' },
          access_token: 'tok123',
        },
      },
      error: null,
    })

    supabase.from.mockReturnValue({
      select: vi.fn().mockReturnThis(),
      eq: vi.fn().mockReturnThis(),
      single: vi.fn().mockResolvedValue({
        data: { roles: { name: 'patient' } },
        error: null,
      }),
    })

    const result = await getSession()

    expect(result).toEqual({
      user: { id: 'user-1', email: 'test@test.com' },
      session: expect.objectContaining({ access_token: 'tok123' }),
      role: 'patient',
    })
  })

  //<------------------- NO SESSION ─────────────────────────────────────────>
  it('returns null when no session exists', async () => {
    supabase.auth.getSession.mockResolvedValue({
      data: { session: null },
      error: null,
    })

    const result = await getSession()
    expect(result).toBeNull()
  })

  //<------------------- SESSION ERROR ──────────────────────────────────────>
  it('returns null when getSession returns an error', async () => {
    supabase.auth.getSession.mockResolvedValue({
      data: { session: null },
      error: { message: 'JWT expired' },
    })

    const result = await getSession()
    expect(result).toBeNull()
  })

  //<------------------- NULL ROLE ───────────────────────────────────────────>
  it('returns null role if user has no role assigned', async () => {
    supabase.auth.getSession.mockResolvedValue({
      data: {
        session: {
          user: { id: 'user-2', email: 'norole@test.com' },
          access_token: 'tok456',
        },
      },
      error: null,
    })

    supabase.from.mockReturnValue({
      select: vi.fn().mockReturnThis(),
      eq: vi.fn().mockReturnThis(),
      single: vi.fn().mockResolvedValue({ data: null, error: null }),
    })

    const result = await getSession()
    expect(result.role).toBeNull()
  })
})


// ─────────────────────────────────────────────────────────────────────────────
// authService — login() edge cases
// ─────────────────────────────────────────────────────────────────────────────

describe('authService - login edge cases', () => {
  beforeEach(() => vi.clearAllMocks())

  //<------------------- UNVERIFIED EMAIL ───────────────────────────────────>
  it('returns user-facing error when email is not confirmed', async () => {
    supabase.auth.signInWithPassword.mockResolvedValue({
      data: null,
      error: { message: 'Email not confirmed' },
    })

    const result = await login('unverified@test.com', 'password123')
    expect(result).toEqual({
      error: 'Please verify your email address before logging in.',
    })
  })

  //<------------------- UNKNOWN ERROR FALLBACK ──────────────────────────────>
  it('returns raw message for unknown Supabase errors', async () => {
    supabase.auth.signInWithPassword.mockResolvedValue({
      data: null,
      error: { message: 'Some unexpected Supabase error' },
    })

    const result = await login('user@test.com', 'password123')
    expect(result.error).toBe('Some unexpected Supabase error')
  })

  //<------------------- ALL THREE ROLES ────────────────────────────────────>
  it.each([
    ['patient', 'patient-1'],
    ['doctor',  'doctor-1'],
    ['admin',   'admin-1'],
  ])('returns role "%s" correctly on successful login', async (role, userId) => {
    supabase.auth.signInWithPassword.mockResolvedValue({
      data: {
        user: { id: userId, email: `${role}@test.com` },
        session: { access_token: 'tok' },
      },
      error: null,
    })

    supabase.from.mockReturnValue({
      select: vi.fn().mockReturnThis(),
      eq: vi.fn().mockReturnThis(),
      single: vi.fn().mockResolvedValue({
        data: { roles: { name: role } },
        error: null,
      }),
    })

    const result = await login(`${role}@test.com`, 'password123')
    expect(result.role).toBe(role)
  })
})


// ─────────────────────────────────────────────────────────────────────────────
// authService — onAuthStateChange()
// ─────────────────────────────────────────────────────────────────────────────

describe('authService - onAuthStateChange', () => {
  beforeEach(() => vi.clearAllMocks())

  //<------------------- CALLS BACK WITH ROLE ON LOGIN ──────────────────────>
  it('calls callback with { user, session, role } on login event', async () => {
    const fakeSession = {
      user: { id: 'user-1', email: 'test@test.com' },
      access_token: 'tok123',
    }

    supabase.auth.onAuthStateChange.mockImplementation((cb) => {
      cb('SIGNED_IN', fakeSession)
      return { data: { subscription: { unsubscribe: vi.fn() } } }
    })

    supabase.from.mockReturnValue({
      select: vi.fn().mockReturnThis(),
      eq: vi.fn().mockReturnThis(),
      single: vi.fn().mockResolvedValue({
        data: { roles: { name: 'doctor' } },
        error: null,
      }),
    })

    const callback = vi.fn()
    onAuthStateChange(callback)

    await waitFor(() => {
      expect(callback).toHaveBeenCalledWith(
        expect.objectContaining({ role: 'doctor' })
      )
    })
  })

  //<------------------- CALLS BACK WITH NULL ON LOGOUT ─────────────────────>
  it('calls callback with null on logout event', () => {
    supabase.auth.onAuthStateChange.mockImplementation((cb) => {
      cb('SIGNED_OUT', null)
      return { data: { subscription: { unsubscribe: vi.fn() } } }
    })

    const callback = vi.fn()
    onAuthStateChange(callback)

    expect(callback).toHaveBeenCalledWith(null)
  })
})


// ─────────────────────────────────────────────────────────────────────────────
// Login component
// ─────────────────────────────────────────────────────────────────────────────

const renderLogin = () =>
  render(
    <MemoryRouter>
      <Login />
    </MemoryRouter>
  )

describe('Login component', () => {
  beforeEach(() => vi.clearAllMocks())

  //<------------------- RENDERS FORM ───────────────────────────────────────>
  it('renders email and password fields and submit button', () => {
    renderLogin()
    expect(screen.getByLabelText(/email address/i)).toBeTruthy()
    expect(screen.getByLabelText("Password")).toBeTruthy()
    expect(screen.getByRole('button', { name: /log in/i })).toBeTruthy()
  })

  //<------------------- SUCCESS: NAVIGATES TO / ────────────────────────────>
  it('navigates to / on successful login', async () => {
    supabase.auth.signInWithPassword.mockResolvedValue({
      data: { user: { id: 'u1' }, session: { access_token: 'tok' } },
      error: null,
    })

    renderLogin()
    fireEvent.change(screen.getByLabelText(/email address/i), {
      target: { value: 'test@test.com' },
    })
    fireEvent.change(screen.getByLabelText("Password"), {
      target: { value: 'password123' },
    })
    fireEvent.click(screen.getByRole('button', { name: /log in/i }))

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/')
    })
  })

  //<------------------- WRONG CREDENTIALS ERROR ────────────────────────────>
  it('shows error message on wrong credentials', async () => {
    supabase.auth.signInWithPassword.mockResolvedValue({
      data: null,
      error: { message: 'Invalid login credentials' },
    })

    renderLogin()
    fireEvent.change(screen.getByLabelText(/email address/i), {
      target: { value: 'wrong@test.com' },
    })
    fireEvent.change(screen.getByLabelText("Password"), {
      target: { value: 'wrongpass' },
    })
    fireEvent.click(screen.getByRole('button', { name: /log in/i }))

    await waitFor(() => {
      expect(screen.getByRole('alert').textContent).toContain(
        'Incorrect email or password.'
      )
    })
  })

  //<------------------- UNVERIFIED EMAIL ERROR ─────────────────────────────>
  it('shows error message when email is not confirmed', async () => {
    supabase.auth.signInWithPassword.mockResolvedValue({
      data: null,
      error: { message: 'Email not confirmed' },
    })

    renderLogin()
    fireEvent.change(screen.getByLabelText(/email address/i), {
      target: { value: 'unverified@test.com' },
    })
    fireEvent.change(screen.getByLabelText("Password"), {
      target: { value: 'password123' },
    })
    fireEvent.click(screen.getByRole('button', { name: /log in/i }))

    await waitFor(() => {
      expect(screen.getByRole('alert').textContent).toContain(
        'Please confirm your email before logging in.'
      )
    })
  })

  //<------------------- LOADING STATE ──────────────────────────────────────>
  it('shows loading state while request is in flight', async () => {
    supabase.auth.signInWithPassword.mockImplementation(
      () => new Promise(() => {}) // never resolves — keeps loading state
    )

    renderLogin()
    fireEvent.change(screen.getByLabelText(/email address/i), {
      target: { value: 'test@test.com' },
    })
    fireEvent.change(screen.getByLabelText("Password"), {
      target: { value: 'password123' },
    })
    fireEvent.click(screen.getByRole('button', { name: /log in/i }))

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /logging in/i }).textContent).toContain('Logging in')
    })
  })

  //<------------------- SUPABASE CALLED WITH CORRECT CREDENTIALS ───────────>
  it('calls supabase.auth.signInWithPassword with correct email and password', async () => {
    supabase.auth.signInWithPassword.mockResolvedValue({
      data: { user: { id: 'u1' }, session: {} },
      error: null,
    })

    renderLogin()
    fireEvent.change(screen.getByLabelText(/email address/i), {
      target: { value: 'doctor@test.com' },
    })
    fireEvent.change(screen.getByLabelText("Password"), {
      target: { value: 'securepass' },
    })
    fireEvent.click(screen.getByRole('button', { name: /log in/i }))

    await waitFor(() => {
      expect(supabase.auth.signInWithPassword).toHaveBeenCalledWith({
        email: 'doctor@test.com',
        password: 'securepass',
      })
    })
  })
})