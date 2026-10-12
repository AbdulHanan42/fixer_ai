<script setup>
import { useAppStore } from '@/stores/app.js'

const app = useAppStore()

const styles = {
  success: 'border-emerald-200 bg-emerald-50 text-emerald-900',
  error: 'border-red-200 bg-red-50 text-red-900',
  info: 'border-blue-200 bg-blue-50 text-blue-900',
}

function dismiss(id) {
  app.removeNotification(id)
}
</script>

<template>
  <div class="pointer-events-none fixed inset-x-0 top-4 z-50 flex flex-col items-center gap-3 px-4 sm:inset-x-auto sm:right-4 sm:items-end"
    aria-live="polite" aria-relevant="additions">
    <div v-for="notification in app.notifications" :key="notification.id" role="status"
      class="pointer-events-auto flex w-full max-w-sm items-start gap-3 rounded-xl border p-4 shadow-lg"
      :class="styles[notification.type] || styles.info">
      <p class="min-w-0 flex-1 text-sm font-medium">{{ notification.message }}</p>
      <button type="button" class="rounded p-1 text-current/70 hover:bg-black/5 hover:text-current"
        :aria-label="`Dismiss ${notification.type || 'notification'}`" @click="dismiss(notification.id)">
        <span aria-hidden="true">✕</span>
      </button>
    </div>
  </div>
</template>
