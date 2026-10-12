const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'

export function createRepairSocket(requestId, token) {
  const url = new URL(API_BASE_URL)
  url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:'
  const apiPath = url.pathname.replace(/\/$/, '')
  url.pathname = `${apiPath}/repairs/${encodeURIComponent(requestId)}/ws`
  url.search = ''
  url.searchParams.set('token', token)
  return new WebSocket(url)
}

export function createNotificationSocket(token) {
  const url = new URL(API_BASE_URL)
  url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:'
  const apiPath = url.pathname.replace(/\/$/, '')
  url.pathname = `${apiPath}/notifications/ws`
  url.search = ''
  url.searchParams.set('token', token)
  return new WebSocket(url)
}
