// api.js — centralized helper for making requests to the Flask backend.
// All API calls should go through this file so the base URL and headers
// are defined in one place. Add new functions below as endpoints are created.

// Base URL for all API requests.
// During development, Vite proxies /api/* to http://localhost:5000 (see vite.config.js).
// In production, set VITE_API_BASE in the frontend .env to the deployed backend URL.
const BASE_URL = import.meta.env.VITE_API_BASE || '/api'

// Generic fetch wrapper — handles JSON parsing and basic error throwing.
async function request(path, options = {}) {
  const response = await fetch(`${BASE_URL}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  })

  if (!response.ok) {
    // Throw an error with the HTTP status so callers can handle it
    throw new Error(`API error: ${response.status} ${response.statusText}`)
  }

  return response.json()
}

// --- Health ---

// Checks that the Flask backend is reachable. Useful for debugging.
export function getHealth() {
  return request('/health')
}

// --- Appointment history ---

// Retrieves appointment history for a given user.
export function getAppointmentHistory(userId) {
  return request(`/appointment-history/${userId}`)
}

// --- Auth / Registration ---

// Syncs a newly registered Supabase user to the local database.
// Called automatically by authService.registerUser after a successful signUp.
// Implements the DB sync step described in issue #193.
export function syncRegistration(userData) {
  return request('/auth/register', {
    method: 'POST',
    body: JSON.stringify(userData),
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
