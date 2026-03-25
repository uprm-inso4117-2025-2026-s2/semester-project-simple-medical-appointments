const BASE_URL = import.meta.env.VITE_API_BASE || '/api'

async function request(path, options = {}) {
  const response = await fetch(`${BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  })
  const data = await response.json()
  if (!response.ok) {
    throw new Error(data.error || `API error: ${response.status}`)
  }
  return data
}


export function createClosure(payload) {
  return request('/closures/', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}


export function listClosures(filters = {}) {
  const params = new URLSearchParams()
  if (filters.type)      params.set('type', filters.type)
  if (filters.doctor_id) params.set('doctor_id', filters.doctor_id)
  const qs = params.toString() ? `?${params.toString()}` : ''
  return request(`/closures/${qs}`)
}


export function deleteClosure(id) {
  return request(`/closures/${id}`, { method: 'DELETE' })
}


export function checkClosure(payload) {
  return request('/closures/check', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}