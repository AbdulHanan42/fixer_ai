import { ref } from 'vue'
import { defineStore } from 'pinia'

export const useAppStore = defineStore('app', () => {
  const isLoading = ref(false)
  const notifications = ref([])

  function setLoading(loading) {
    isLoading.value = loading
  }

  function addNotification(notification) {
    notifications.value.push(notification)
  }

  function removeNotification(id) {
    notifications.value = notifications.value.filter((n) => n.id !== id)
  }

  return { isLoading, notifications, setLoading, addNotification, removeNotification }
})
