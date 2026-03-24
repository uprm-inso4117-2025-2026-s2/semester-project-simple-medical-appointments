import { supabase } from '../lib/supabaseClient'

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
function formatAuthError(error) {
  switch (error.message) {
    case 'Invalid login credentials':
      return 'Incorrect email or password.'
    case 'Email not confirmed':
      return 'Please verify your email address before logging in.'
    case 'User not found':
      return 'No account found with that email.'
    case 'Too many requests':
      return 'Too many attempts. Please wait a moment and try again.'
    default:
      return error.message ?? 'An unexpected error occurred.'
  }
}

// ─────────────────────────────────────────────
// Public API
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
    return { error: formatAuthError(error) }
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
