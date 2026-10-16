import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import http from '@/api/http.js'
import { createRepairSocket } from '@/api/websocket.js'

export const useChatStore = defineStore('chat', () => {
  const activeRequestId = ref(null)
  const messages = ref([])
  const connectionState = ref('disconnected')
  const error = ref('')
  const isConnected = computed(() => connectionState.value === 'connected')
  let socket = null
  let reconnectTimer = null
  let reconnectAttempt = 0
  let intentionalClose = false

  function appendMessage(message) {
    if (!message?.id || messages.value.some((item) => item.id === message.id)) return
    messages.value = [...messages.value, message].sort((a, b) => new Date(a.sent_at) - new Date(b.sent_at))
  }

  function openSocket(requestId, token) {
    if (activeRequestId.value !== requestId || !token) return
    connectionState.value = 'connecting'
    socket = createRepairSocket(requestId, token)
    socket.onopen = () => {
      reconnectAttempt = 0
      connectionState.value = 'connected'
      error.value = ''
    }
    socket.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data)
        if (payload.type === 'message') appendMessage(payload.data)
        if (payload.type === 'error') error.value = payload.detail || 'Could not send the message.'
      } catch {
        error.value = 'Received an unreadable chat message.'
      }
    }
    socket.onerror = () => { error.value = 'Chat connection problem. Reconnecting...' }
    socket.onclose = async () => {
      socket = null
      if (intentionalClose || activeRequestId.value !== requestId) {
        connectionState.value = 'disconnected'
        return
      }
      connectionState.value = 'reconnecting'
      reconnectAttempt += 1
      const delay = Math.min(1000 * (2 ** (reconnectAttempt - 1)), 20000)
      reconnectTimer = window.setTimeout(async () => {
        try {
          const history = await http.get(`/repairs/${requestId}/messages`, { params: { skip: 0, limit: 100 } })
          if (activeRequestId.value === requestId) {
            for (const message of history.messages || []) appendMessage(message)
          }
        } catch {
          // The socket reconnect remains useful even if history is temporarily unavailable.
        }
        openSocket(requestId, token)
      }, delay)
    }
  }

  async function connect(requestId, token) {
    disconnect()
    intentionalClose = false
    activeRequestId.value = requestId
    messages.value = []
    error.value = ''
    connectionState.value = 'connecting'
    try {
      const history = await http.get(`/repairs/${requestId}/messages`, { params: { skip: 0, limit: 100 } })
      if (activeRequestId.value === requestId) messages.value = history.messages || []
    } catch (err) {
      if (activeRequestId.value === requestId) error.value = err.message || 'Could not load chat history.'
    }
    if (activeRequestId.value === requestId) openSocket(requestId, token)
  }

  function send(content) {
    const message = content.trim()
    if (!message || !socket || socket.readyState !== WebSocket.OPEN) return false
    socket.send(JSON.stringify({ type: 'message', content: message }))
    return true
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
    connectionState.value = 'disconnected'
  }

  return { activeRequestId, messages, connectionState, error, isConnected, connect, disconnect, send }
})
