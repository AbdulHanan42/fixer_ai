<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { useAuthStore } from '@/stores/auth.js'
import { useChatStore } from '@/stores/chat.js'

const props = defineProps({ requestId: { type: String, required: true } })
const auth = useAuthStore()
const chat = useChatStore()
const draft = ref('')
const messageList = ref(null)
const sendingLocation = ref(false)
const locationError = ref('')
const connected = computed(() => chat.activeRequestId === props.requestId && chat.isConnected)

function locationUrl(content) {
  if (typeof content !== 'string' || !content.startsWith('LOCATION_SHARE:')) return null
  const url = content.slice('LOCATION_SHARE:'.length).trim()
  try {
    const parsed = new URL(url)
    const coordinates = parsed.searchParams.get('q')?.split(',').map(Number)
    if (parsed.protocol !== 'https:' || parsed.hostname !== 'www.google.com' || parsed.pathname !== '/maps' || coordinates?.length !== 2 || coordinates.some((value) => !Number.isFinite(value))) return null
    return url
  } catch {
    return null
  }
}

function sendCurrentLocation() {
  locationError.value = ''
  if (!connected.value) {
    locationError.value = 'Chat is reconnecting. Please try again when it is connected.'
    return
  }
  if (!navigator.geolocation) {
    locationError.value = 'Location sharing is not supported by this browser.'
    return
  }
  sendingLocation.value = true
  navigator.geolocation.getCurrentPosition(
    ({ coords }) => {
      const mapUrl = `https://www.google.com/maps?q=${coords.latitude},${coords.longitude}`
      if (!chat.send(`LOCATION_SHARE:${mapUrl}`)) locationError.value = 'Could not send your location. Check the chat connection and try again.'
      sendingLocation.value = false
    },
    (error) => {
      locationError.value = error.code === 1
        ? 'Location permission was denied. Allow location access in your browser and try again.'
        : error.code === 2
          ? 'Your location is unavailable right now. Please try again.'
          : error.code === 3
            ? 'Location request timed out. Please try again.'
            : 'Could not get your location. Please try again.'
      sendingLocation.value = false
    },
    { enableHighAccuracy: true, timeout: 15000, maximumAge: 0 },
  )
}

async function scrollToLatest() {
  await nextTick()
  if (messageList.value) messageList.value.scrollTop = messageList.value.scrollHeight
}

function sendMessage() {
  if (!chat.send(draft.value)) return
  draft.value = ''
}

function handleSubmit(event) {
  if (event.shiftKey) return
  event.preventDefault()
  sendMessage()
}

watch(() => chat.messages.length, scrollToLatest)
onMounted(() => chat.connect(props.requestId, auth.token))
onUnmounted(() => chat.disconnect())
</script>

<template>
  <section class="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-xl shadow-slate-900/5 [transform:perspective(1400px)_rotateX(.35deg)]">
    <header class="flex items-center justify-between border-b border-slate-100 bg-gradient-to-r from-slate-950 to-slate-800 px-5 py-4 text-white">
      <div><p class="text-[10px] font-bold uppercase tracking-[.2em] text-blue-300">Repair conversation</p><h3 class="mt-1 text-sm font-bold">Request #{{ requestId.slice(0, 8) }}</h3></div>
      <span class="flex items-center gap-2 rounded-full bg-white/10 px-3 py-1.5 text-[11px] font-semibold"><span :class="connected ? 'bg-emerald-400' : 'bg-amber-300'" class="size-1.5 animate-pulse rounded-full"></span>{{ chat.connectionState }}</span>
    </header>
    <div ref="messageList" class="flex h-72 flex-col gap-3 overflow-y-auto bg-slate-50/80 p-4 sm:h-80">
      <p v-if="!chat.messages.length" class="m-auto max-w-52 text-center text-xs leading-5 text-slate-400">Messages between you and the other participant will appear here.</p>
      <article v-for="message in chat.messages" :key="message.id" class="flex" :class="message.sender_id === auth.user?.id ? 'justify-end' : 'justify-start'">
        <div class="max-w-[85%] rounded-2xl px-3.5 py-2.5 shadow-sm" :class="message.sender_id === auth.user?.id ? 'rounded-br-md bg-blue-600 text-white' : 'rounded-bl-md border border-slate-200 bg-white text-slate-800'">
          <p v-if="message.sender_id !== auth.user?.id" class="mb-1 text-[10px] font-bold text-blue-700">{{ message.sender_name || 'Repair partner' }}</p>
          <div v-if="locationUrl(message.content)" class="min-w-52 rounded-xl border border-white/20 bg-white/10 p-3">
            <p class="text-sm font-semibold">📍 Shared location</p>
            <a :href="locationUrl(message.content)" target="_blank" rel="noopener noreferrer" class="mt-2 inline-flex items-center rounded-lg bg-white px-3 py-2 text-xs font-bold text-blue-700 transition hover:bg-blue-50">View on Map <span class="ml-1" aria-hidden="true">↗</span></a>
          </div>
          <p v-else class="whitespace-pre-wrap break-words text-sm leading-5">{{ message.content }}</p>
          <time class="mt-1 block text-right text-[10px]" :class="message.sender_id === auth.user?.id ? 'text-blue-100' : 'text-slate-400'">{{ new Date(message.sent_at).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' }) }}</time>
        </div>
      </article>
    </div>
    <p v-if="chat.error" class="px-4 pt-2 text-xs text-amber-700" role="status">{{ chat.error }}</p>
    <p v-if="locationError" class="px-4 pt-2 text-xs text-amber-700" role="alert">{{ locationError }}</p>
    <form class="flex items-end gap-2 border-t border-slate-100 p-3" @submit="handleSubmit">
      <textarea v-model="draft" rows="1" maxlength="2000" aria-label="Message" placeholder="Write a message…" class="max-h-24 min-h-11 flex-1 resize-y rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-3 text-sm outline-none transition focus:border-blue-400 focus:bg-white focus:ring-4 focus:ring-blue-50" @keydown.enter="handleSubmit"></textarea>
      <button type="button" :disabled="!connected || sendingLocation" class="grid size-11 shrink-0 place-items-center rounded-xl border border-slate-200 bg-white text-lg text-slate-700 transition hover:border-blue-300 hover:bg-blue-50 disabled:cursor-not-allowed disabled:opacity-40" :aria-label="sendingLocation ? 'Getting current location' : 'Send current location'" :title="sendingLocation ? 'Getting your location…' : 'Send current location'" @click="sendCurrentLocation"><span v-if="sendingLocation" class="size-4 animate-spin rounded-full border-2 border-blue-200 border-t-blue-600" aria-hidden="true"></span><span v-else aria-hidden="true">📍</span></button>
      <button type="submit" :disabled="!connected || !draft.trim()" class="grid size-11 shrink-0 place-items-center rounded-xl bg-blue-600 text-lg text-white shadow-lg shadow-blue-600/20 transition hover:-translate-y-0.5 hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-40" aria-label="Send message">↑</button>
    </form>
  </section>
</template>
