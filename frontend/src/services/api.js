// api.js — centralized helper for making requests to the Flask backend.
// All API calls should go through this file so the base URL and headers
// are defined in one place. Add new functions below as endpoints are created.

import { supabase } from '../lib/supabaseClient'

// Base URL for all API requests.
// During development, Vite proxies /api/* to http://localhost:5000 (see vite.config.js).
// In production, set VITE_API_BASE in the frontend .env to the deployed backend URL.
const BASE_URL = import.meta.env.VITE_API_BASE || '/api'

// Generic fetch wrapper — handles JSON parsing and basic error throwing.
async function request(path, options = {}) {
  const {
    headers: customHeaders = {},
    skipAuth = false,
    ...restOptions
  } = options

  let authHeaders = {}
  if (!skipAuth) {
    const {
      data: { session },
    } = await supabase.auth.getSession()

    if (session?.access_token) {
      authHeaders = { Authorization: `Bearer ${session.access_token}` }
    }
  }

  const response = await fetch(`${BASE_URL}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...authHeaders,
      ...customHeaders,
    },
    ...restOptions,
  })

  if (!response.ok) {
    // Throw an error with the HTTP status so callers can handle it
    let message = `API error: ${response.status} ${response.statusText}`
    try {
      const body = await response.json()
      if (body.error) message = body.error
    } catch (_) { /* ignore */ }
    const err = new Error(message)
    err.status = response.status
    throw err
  }

  return response.json()
}

// --- Health ---

// Checks that the Flask backend is reachable. Useful for debugging.
export function getHealth() {
  return request('/health', { skipAuth: true })
}

// --- Appointment history ---

// Retrieves all appointment history (patient_id, doctor_name, clinic_name, status, date).
export function getAllAppointmentHistory() {
  return request('/appointment-history')
}

// Retrieves appointment history for a specific patient.
export function getAppointmentHistory(patientId) {
  return request(`/appointment-history/${patientId}`)
}

// --- Auth / Registration ---

// Syncs a newly registered Supabase user to the local database.
// Called automatically by authService.registerUser after a successful signUp.
// Implements the DB sync step described in issue #193.
export function syncRegistration(userData) {
  return request('/auth/register', {
    method: 'POST',
    skipAuth: true,
    body: JSON.stringify(userData),
  })
}

// --- Profile ---

export function getProfile(userId) {
  return request(`/profile/${userId}`)
}

export function updateProfile(userId, updates) {
  return request(`/profile/${userId}`, {
    method: 'PUT',
    body: JSON.stringify(updates),
  })
}

// Fetch all appointments 
export function getAppointments(status = '') {
  const qs = status ? `?status=${encodeURIComponent(status)}` : ''
  return request(`/appointments${qs}`)
}

// Fetch a single appointment by id 
export function getAppointment(id) {
  return request(`/appointments/${id}`)
}

/**
 * Cancel an appointment.
 * @param {number} id - Appointment ID
 * @param {string} reason - Optional cancellation reason
 * @param {number|null} cancelledById - ID of the admin performing the action
 */
export function cancelAppointment(id, reason = '', cancelledById = null) {
  return request(`/appointments/${id}/cancel`, {
    method: 'PUT',
    body: JSON.stringify({ reason, cancelled_by_id: cancelledById }),
  })
}

// --- Add new API functions below as routes are created in Flask ---
// Example:
// export function getAppointments() {
//   return request('/appointments')
// }
//
// export function createAppointment(data) {
//   return request('/appointments', { method: 'POST', body: JSON.stringify(data) })
// }