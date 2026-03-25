import { supabase } from '../lib/supabaseClient'
import { syncRegistration } from './api'

// ─────────────────────────────────────────────
// Internal helpers
// ─────────────────────────────────────────────

/**
 * Fetches the role name for a given user from public.user_roles.
 * Returns null if the user has no role assigned yet.
 */
async function getUserRole(userId) {
  const { data, error } = await supabase
    .from('user_roles')
    .select('roles(name)')
    .eq('user_id', userId)
    .single()

  if (error || !data) return null
  return data.roles?.name ?? null
}

/**
 * Maps raw Supabase Auth error messages to user-facing strings.
 */
function formatAuthError(message) {
  const messages = {
    'Invalid login credentials':                        'Incorrect email or password.',
    'Email not confirmed':                              'Please verify your email address before logging in.',
    'User not found':                                   'No account found with that email.',
    'Too many requests':                                'Too many attempts. Please wait a moment and try again.',
    'User already registered':                          'An account with this email already exists.',
    'Password should be at least 6 characters':         'Password must be at least 6 characters long.',
    'Unable to validate email address: invalid format': 'Please enter a valid email address.',
    'Signup requires a valid password':                 'Please enter a valid password.',
  }
  return messages[message] || message || 'An unexpected error occurred. Please try again.'
}

// ─────────────────────────────────────────────
// Registration
// ─────────────────────────────────────────────

/**
 * Register a new user with email and password.
 *
 * Flow:
 *   1. Calls supabase.auth.signUp to create the auth record.
 *   2. On success, calls the backend /api/auth/register to sync the user to the DB.
 *
 * Returns: { user, session, emailConfirmationRequired }
 * Throws:  Error with a user-friendly message on failure.
 */
export async function registerUser(email, password) {
  const { data, error } = await supabase.auth.signUp({ email, password })

  if (error) {
    throw new Error(formatAuthError(error.message))
  }

  const { user, session } = data

  if (user) {
    try {
      await syncRegistration({ supabase_uid: user.id, email: user.email })
    } catch (syncError) {
      console.error('DB sync failed after registration:', syncError.message)
    }
  }

  return {
    user,
    session,
    emailConfirmationRequired: !!user && !session,
  }
}

// ─────────────────────────────────────────────
// Login & Logout
// ─────────────────────────────────────────────

/**
 * Signs in with email and password.
 *
 * On success returns: { user, session, role }
 * On failure returns: { error }  (user-friendly string)
 */
export async function login(email, password) {
  const { data, error } = await supabase.auth.signInWithPassword({
    email,
    password,
  })

  if (error) {
    return { error: formatAuthError(error.message) }
  }

  const role = await getUserRole(data.user.id)
  return { user: data.user, session: data.session, role }
}

/**
 * Signs out the current user and clears the local Supabase session.
 *
 * On success returns: { success: true }
 * On failure returns: { error }
 */
export async function logout() {
  const { error } = await supabase.auth.signOut()

  if (error) {
    return { error: error.message }
  }

  return { success: true }
}

// ─────────────────────────────────────────────
// Session
// ─────────────────────────────────────────────

/**
 * Returns the current active session with role, or null if not authenticated.
 * Use this on app load to restore session state.
 *
 * On success returns: { user, session, role }
 * When no session:    null
 */
export async function getSession() {
  const {
    data: { session },
    error,
  } = await supabase.auth.getSession()

  if (error || !session) return null

  const role = await getUserRole(session.user.id)
  return { user: session.user, session, role }
}

/**
 * Subscribes to auth state changes (login, logout, token refresh).
 * Call this once at the app root to keep session state in sync.
 *
 * Usage:
 *   const { data: { subscription } } = onAuthStateChange((session) => {
 *     // update your global auth state here
 *   })
 *   // cleanup: subscription.unsubscribe()
 *
 * The callback receives { user, session, role } or null on logout.
 */
export function onAuthStateChange(callback) {
  return supabase.auth.onAuthStateChange(async (event, session) => {
    if (!session) {
      callback(null)
      return
    }

    const role = await getUserRole(session.user.id)
    callback({ user: session.user, session, role })
  })
}
