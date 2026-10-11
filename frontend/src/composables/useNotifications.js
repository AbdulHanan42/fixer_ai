import { useAppStore } from '@/stores/app.js'

export function useNotifications() {
  const appStore = useAppStore()

  function showNotification(notification) {
    const id = Date.now()
    appStore.addNotification({ id, ...notification })

    setTimeout(() => {
      appStore.removeNotification(id)
    }, 5000)
  }

  function showError(message) {
    showNotification({ type: 'error', message })
  }

  function showSuccess(message) {
    showNotification({ type: 'success', message })
  }

  function showInfo(message) {
    showNotification({ type: 'info', message })
  }

  return {
    notifications: appStore.notifications,
    showNotification,
    showError,
    showSuccess,
    showInfo,
  }
}
