const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'

async function request(endpoint, options = {}) {
  const url = `${API_BASE_URL}${endpoint}`
  const config = {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  }

  const response = await fetch(url, config)

  if (!response.ok) {
    const error = new Error(`HTTP error! status: ${response.status}`)
    error.response = response
    throw error
  }

  return response.json()
}

export default {
  get: (endpoint, options) => request(endpoint, { ...options, method: 'GET' }),
  post: (endpoint, data, options) =>
    request(endpoint, { ...options, method: 'POST', body: JSON.stringify(data) }),
  put: (endpoint, data, options) =>
    request(endpoint, { ...options, method: 'PUT', body: JSON.stringify(data) }),
  patch: (endpoint, data, options) =>
    request(endpoint, { ...options, method: 'PATCH', body: JSON.stringify(data) }),
  delete: (endpoint, options) => request(endpoint, { ...options, method: 'DELETE' }),
}
