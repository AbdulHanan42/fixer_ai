import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import http from '@/api/http.js'
import { createNotificationSocket } from '@/api/websocket.js'

export const useNotificationsStore = defineStore('notifications', () => {
  const items = ref([])
  const unreadCount = ref(0)
  const connectionState = ref('disconnected')
  const isLoading = ref(false)
  const unreadItems = computed(() => items.value.filter((item) => !item.is_read))
  let socket = null
  let reconnectTimer = null
  let activeToken = null
  let intentionalClose = false
  let reconnectAttempt = 0

  function mergeNotification(notification) {
    if (!notification?.id) return
    const existing = items.value.findIndex((item) => item.id === notification.id)
    if (existing >= 0) {
      items.value[existing] = { ...items.value[existing], ...notification }
      return
    }
    items.value = [notification, ...items.value].slice(0, 50)
    if (!notification.is_read) unreadCount.value += 1
  }

  async function load() {
    isLoading.value = true
    try {
      const result = await http.get('/notifications', { params: { skip: 0, limit: 20 } })
      items.value = result.notifications || []
      unreadCount.value = result.unread_count || 0
    } finally {
      isLoading.value = false
    }
  }

  function connect(token) {
    if (!token || (socket && activeToken === token)) return
    disconnect()
    activeToken = token
    intentionalClose = false
    connectionState.value = 'connecting'
    socket = createNotificationSocket(token)
    socket.onopen = () => {
      reconnectAttempt = 0
      connectionState.value = 'connected'
    }
    socket.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data)
        if (payload.type === 'connected') unreadCount.value = payload.unread_count ?? unreadCount.value
        if (payload.type === 'notification') mergeNotification(payload.data)
      } catch {
        // Ignore malformed frames and keep the notification stream alive.
      }
    }
    socket.onerror = () => { connectionState.value = 'reconnecting' }
    socket.onclose = () => {
      socket = null
      if (intentionalClose) {
        connectionState.value = 'disconnected'
        return
      }
      connectionState.value = 'reconnecting'
      reconnectAttempt += 1
      const wait = Math.min(1000 * (2 ** (reconnectAttempt - 1)), 20000)
      reconnectTimer = window.setTimeout(async () => {
        try { await load() } catch { /* Retry the live stream even when REST is temporarily unavailable. */ }
        connect(activeToken)
      }, wait)
    }
  }

  async function markRead(id) {
    const wasUnread = items.value.find((item) => item.id === id)?.is_read === false
    const updated = await http.put(`/notifications/${id}/read`)
    mergeNotification(updated)
    if (wasUnread) unreadCount.value = Math.max(0, unreadCount.value - 1)
    return updated
  }

  async function markAllRead() {
    const result = await http.put('/notifications/read-all')
    items.value = items.value.map((item) => ({ ...item, is_read: true }))
    unreadCount.value = 0
    return result
  }

  function disconnect() {
    intentionalClose = true
    if (reconnectTimer) window.clearTimeout(reconnectTimer)
    reconnectTimer = null
    if (socket) {
      const current = socket
      socket = null
      current.onopen = null
      current.onmessage = null
      current.onerror = null
      current.onclose = null
      current.close()
    }
    activeToken = null
    connectionState.value = 'disconnected'
  }

  return { items, unreadCount, unreadItems, connectionState, isLoading, load, connect, disconnect, markRead, markAllRead }
})
