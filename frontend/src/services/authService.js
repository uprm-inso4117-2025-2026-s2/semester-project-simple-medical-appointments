// authService.js — handles Supabase Auth sign-up and triggers backend DB sync.
// All authentication operations should go through this file.

import { supabase } from '../lib/supabaseClient'
import { syncRegistration } from './api'

// Maps Supabase error messages to user-friendly strings.
const ERROR_MESSAGES = {
  'User already registered': 'An account with this email already exists.',
  'Password should be at least 6 characters': 'Password must be at least 6 characters long.',
  'Unable to validate email address: invalid format': 'Please enter a valid email address.',
  'Signup requires a valid password': 'Please enter a valid password.',
}

function getFriendlyError(message) {
  return ERROR_MESSAGES[message] || message || 'An unexpected error occurred. Please try again.'
}

/**
 * Register a new user with email and password.
 *
 * Flow:
 *   1. Calls supabase.auth.signUp to create the auth record.
 *   2. On success, calls the backend /api/auth/register to sync the user to the DB.
 *
 * @param {string} email
 * @param {string} password
 * @returns {{ user, session, emailConfirmationRequired: boolean }}
 * @throws Error with a user-friendly message on failure
 */
export async function registerUser(email, password) {
  const { data, error } = await supabase.auth.signUp({ email, password })

  if (error) {
    throw new Error(getFriendlyError(error.message))
  }

  const { user, session } = data

  // Sync the new user to the local database via the backend registration service.
  if (user) {
    try {
      await syncRegistration({ supabase_uid: user.id, email: user.email })
    } catch (syncError) {
      // Log sync failures but do not block the user — auth succeeded.
      console.error('DB sync failed after registration:', syncError.message)
    }
  }

  // When Supabase email confirmation is enabled, session is null until the user
  // clicks the confirmation link. Signal this to the caller.
  return {
    user,
    session,
    emailConfirmationRequired: !!user && !session,
  }
}
