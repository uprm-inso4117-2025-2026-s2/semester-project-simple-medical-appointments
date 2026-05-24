import { describe, it, expect, vi, beforeEach } from 'vitest'
import { login, logout } from '../services/authService'


/**
  These tests validate the authService logic (frontend authentication layer).
  We are testing both login and logout behavior while mocking Supabase.

  <--------LOGIN TESTS-------->
  - Successful login:
    - Returns user, session, and role
    - Mocks Supabase signInWithPassword and role lookup (supabase.from chain)

  - Failed login:
    - Returns a formatted error message instead of raw Supabase error

  - Missing role case:
    - Ensures system handles users without assigned roles (returns null role)

  <--------LOGOUT TEST----------> 
  - Successful logout:
    - Returns { success: true }
    - Confirms supabase.auth.signOut is called

  - Failed logout:
    - Returns the error message from Supabase

  <--------MOCKING STRATEGY-------->
  - Supabase is fully mocked using vi.mock()
  - Prevents real network/database calls
  - Allows controlled simulation of auth and database responses

*/
 
//For testing go to backend directory in terminal: cd frontend
//Run the test file with or equivalent: npx vitest run src/test/auth.test.js 





//SUPABASE MOCK
vi.mock('../lib/supabaseClient', () => ({
  supabase: {
    auth: {
      signInWithPassword: vi.fn(),
      signOut: vi.fn(),
    },
    from: vi.fn(),
  },
}))

// SUPER IMPORTANT: we mock getUserRole indirectly by mocking supabase.from chain because getUserRole is internal

import { supabase } from '../lib/supabaseClient'

describe('authService - login', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  //---------------- LOGIN SUCCESS CASE ----------------
  it('returns user, session and role on successful login', async () => {
    // 1. Mock login success
    supabase.auth.signInWithPassword.mockResolvedValue({
      data: {
        user: { id: 'user-1', email: 'test@test.com' },
        session: { access_token: 'abc123' },
      },
      error: null,
    })

    // 2. Mock role query (supabase.from chain)
    supabase.from.mockReturnValue({
      select: vi.fn().mockReturnThis(),
      eq: vi.fn().mockReturnThis(),
      single: vi.fn().mockResolvedValue({
        data: {
          roles: { name: 'doctor' },
        },
        error: null,
      }),
    })

    const result = await login('test@test.com', 'password123')

    expect(result).toEqual({
      user: { id: 'user-1', email: 'test@test.com' },
      session: { access_token: 'abc123' },
      role: 'doctor',
    })

    expect(supabase.auth.signInWithPassword).toHaveBeenCalledWith({
      email: 'test@test.com',
      password: 'password123',
    })
  })

  // ---------------- LOGIN ERROR CASE ----------------
  it('returns formatted error when login fails', async () => {
    supabase.auth.signInWithPassword.mockResolvedValue({
      data: null,
      error: { message: 'Invalid login credentials' },
    })

    const result = await login('wrong@test.com', 'wrongpass')

    expect(result).toEqual({
      error: 'Incorrect email or password.',
    })
  })


  //---------------- ROLE NULL CASE ----------------
  it('returns null role if user has no role assigned', async () => {
    supabase.auth.signInWithPassword.mockResolvedValue({
      data: {
        user: { id: 'user-2', email: 'test@test.com' },
        session: { access_token: 'abc123' },
      },
      error: null,
    })

    supabase.from.mockReturnValue({
      select: vi.fn().mockReturnThis(),
      eq: vi.fn().mockReturnThis(),
      single: vi.fn().mockResolvedValue({
        data: null,
        error: null,
      }),
    })

    const result = await login('test@test.com', 'password123')

    expect(result.role).toBeNull()
  })
})


describe('authService - logout', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  //----------------------SUCCESS CASE-----------------
  it('returns success true when logout succeeds', async () => {

  // Arrange
  supabase.auth.signOut.mockResolvedValue({
    error: null,
  })

  // Act
  const result = await logout()

  // Assert
  expect(result).toEqual({
    success: true,
  })

  expect(supabase.auth.signOut).toHaveBeenCalled()
  })

  //----------------------SUCCESS CASE-----------------

  it('returns error message when logout fails', async () => {

  // Arrange
  supabase.auth.signOut.mockResolvedValue({
    error: {
      message: 'Network error',
    },
  })

  // Act
  const result = await logout()

  // Assert
  expect(result).toEqual({
    error: 'Network error',
    })
  })



})