<script setup>
import { onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth.js'
import { useNotificationsStore } from '@/stores/notifications.js'

const auth = useAuthStore()
const notifications = useNotificationsStore()
const router = useRouter()
const open = ref(false)
const actionError = ref('')
let disposed = false

const iconByType = {
  new_repair_request: '🔧',
  request_accepted: '✓',
  request_rejected: '!',
  status_changed: '↻',
  new_message: '✉',
  repair_completed: '★',
}

async function openNotification(item) {
  actionError.value = ''
  if (!item.is_read) {
    try {
      await notifications.markRead(item.id)
    } catch (error) {
      actionError.value = error.message || 'Could not mark this notification as read.'
    }
  }
  open.value = false
  const path = auth.isMechanic ? '/mechanic/dashboard' : auth.isAdmin ? '/admin/dashboard' : '/customer/dashboard'
  const query = item.type === 'new_message' && item.reference_id ? { chat: item.reference_id } : undefined
  await router.push({ path, query })
}

async function markAllRead() {
  actionError.value = ''
  try {
    await notifications.markAllRead()
  } catch (error) {
    actionError.value = error.message || 'Could not mark notifications as read.'
  }
}

onMounted(async () => {
  try {
    await notifications.load()
  } catch {
    // Keep the rest of the workspace available when notifications are offline.
  }
  if (!disposed) notifications.connect(auth.token)
})
onUnmounted(() => {
  disposed = true
  notifications.disconnect()
})
</script>

<template>
  <div class="relative mt-3">
    <button type="button" class="flex w-full items-center gap-3 rounded-xl px-3 py-3 text-sm font-semibold text-slate-400 transition hover:bg-white/[.07] hover:text-white" :aria-expanded="open" @click="open = !open">
      <span class="relative grid size-8 place-items-center rounded-lg bg-white/[.05]">
        <svg class="size-[18px]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M10 21h4" /></svg>
        <span v-if="notifications.unreadCount" class="absolute -right-1 -top-1 grid min-w-4 place-items-center rounded-full bg-rose-500 px-1 text-[9px] font-black leading-4 text-white">{{ notifications.unreadCount > 99 ? '99+' : notifications.unreadCount }}</span>
      </span>
      Notifications<span class="ml-auto text-xs text-slate-500">{{ notifications.connectionState === 'connected' ? 'Live' : '' }}</span>
    </button>

    <section v-if="open" class="absolute left-0 top-full z-[70] mt-2 w-[min(23rem,calc(100vw-2rem))] overflow-hidden rounded-2xl border border-slate-200 bg-white text-slate-900 shadow-2xl shadow-slate-950/30" aria-label="Notifications">
      <header class="flex items-center justify-between border-b border-slate-100 px-4 py-3">
        <div><h2 class="text-sm font-bold">Notifications</h2><p class="mt-0.5 text-[11px] text-slate-500">{{ notifications.unreadCount }} unread</p></div>
        <button type="button" class="text-xs font-bold text-blue-700 hover:text-blue-900 disabled:opacity-40" :disabled="!notifications.unreadCount" @click="markAllRead">Mark all read</button>
      </header>
      <p v-if="actionError" role="alert" class="px-4 pt-3 text-xs text-rose-700">{{ actionError }}</p>
      <div class="max-h-[min(28rem,65vh)] overflow-y-auto p-2">
        <div v-if="notifications.isLoading && !notifications.items.length" class="p-6 text-center text-sm text-slate-500">Loading notifications…</div>
        <div v-else-if="!notifications.items.length" class="p-7 text-center"><span class="text-2xl">✧</span><p class="mt-2 text-sm font-semibold text-slate-700">You’re all caught up</p><p class="mt-1 text-xs text-slate-400">Updates about repairs and messages will show here.</p></div>
        <button v-for="item in notifications.items" :key="item.id" type="button" class="flex w-full gap-3 rounded-xl p-3 text-left transition hover:bg-slate-50" :class="item.is_read ? 'opacity-70' : 'bg-blue-50/70'" @click="openNotification(item)">
          <span class="grid size-9 shrink-0 place-items-center rounded-xl bg-white text-sm font-bold text-blue-700 shadow-sm">{{ iconByType[item.type] || '•' }}</span>
          <span class="min-w-0 flex-1"><span class="flex items-center gap-2"><span class="truncate text-xs font-bold text-slate-800">{{ item.title }}</span><span v-if="!item.is_read" class="size-1.5 shrink-0 rounded-full bg-blue-600"></span></span><span class="mt-1 block line-clamp-2 text-xs leading-5 text-slate-500">{{ item.content }}</span><time class="mt-1.5 block text-[10px] text-slate-400">{{ new Date(item.created_at).toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' }) }}</time></span>
        </button>
      </div>
      <footer class="border-t border-slate-100 px-4 py-2"><span class="text-[10px] text-slate-400">{{ notifications.connectionState === 'connected' ? 'Live updates enabled' : 'Connecting to live updates…' }}</span></footer>
    </section>
  </div>
</template>
