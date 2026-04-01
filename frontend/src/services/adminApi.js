// adminApi.js — API functions for admin user management endpoints.
// All calls require an authenticated admin session; the Bearer token is
// attached automatically from the active Supabase session.

import { supabase } from '../lib/supabaseClient'

const BASE_URL = import.meta.env.VITE_API_BASE || '/api'

async function adminRequest(path, options = {}) {
  const {
    data: { session },
  } = await supabase.auth.getSession()

  const response = await fetch(`${BASE_URL}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(session?.access_token ? { Authorization: `Bearer ${session.access_token}` } : {}),
    },
    ...options,
  })

  // Try to extract a meaningful error message from the JSON body
  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    throw new Error(body.error || body.message || `Request failed: ${response.status} ${response.statusText}`)
  }

  return response.json()
}

/**
 * GET /api/admin/users
 * Returns paginated, filterable user list.
 */
export function listAdminUsers({ page = 1, perPage = 20, role, status } = {}) {
  const params = new URLSearchParams({ page, per_page: perPage })
  if (role)   params.set('role', role)
  if (status) params.set('status', status)
  return adminRequest(`/admin/users?${params}`)
}

/**
 * PUT /api/admin/users/:userId/role
 * Body: { role: 'patient' | 'doctor' | 'admin' }
 */
export function changeUserRole(userId, role) {
  return adminRequest(`/admin/users/${userId}/role`, {
    method: 'PUT',
    body: JSON.stringify({ role }),
  })
}

/**
 * PUT /api/admin/users/:userId/deactivate
 * Bans the user indefinitely (~100 years).
 */
export function deactivateUser(userId) {
  return adminRequest(`/admin/users/${userId}/deactivate`, { method: 'PUT' })
}

/**
 * DELETE /api/admin/users/:userId
 * Permanently removes the user from auth and all DB tables.
 */
export function deleteUser(userId) {
  return adminRequest(`/admin/users/${userId}`, { method: 'DELETE' })
}
