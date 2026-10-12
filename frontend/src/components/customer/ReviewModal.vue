<script setup>
import { ref, watch } from 'vue'
import http from '@/api/http.js'
import { useNotifications } from '@/composables/useNotifications.js'

const props = defineProps({ request: { type: Object, required: true } })
const emit = defineEmits(['submitted', 'close'])
const rating = ref(5)
const comment = ref('')
const submitting = ref(false)
const error = ref('')
const { showSuccess } = useNotifications()

watch(() => props.request?.id, () => { rating.value = 5; comment.value = ''; error.value = '' })

async function submitReview() {
  error.value = ''
  submitting.value = true
  try {
    await http.post('/reviews', { request_id: props.request.id, rating: rating.value, comment: comment.value.trim() })
    showSuccess('Thanks for sharing your experience.')
    emit('submitted', props.request.id)
  } catch (err) {
    error.value = err.message || 'Could not submit your review.'
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="fixed inset-0 z-[60] grid place-items-center bg-slate-950/60 p-4 backdrop-blur-sm" role="presentation" @click.self="$emit('close')">
    <section role="dialog" aria-modal="true" aria-labelledby="review-title" class="w-full max-w-lg overflow-hidden rounded-3xl border border-white/40 bg-white shadow-2xl shadow-slate-950/30 [transform:perspective(1000px)_rotateX(1deg)]">
      <div class="bg-gradient-to-br from-blue-700 via-indigo-700 to-slate-900 p-6 text-white sm:p-8">
        <p class="text-xs font-bold uppercase tracking-[.2em] text-blue-200">Repair complete</p>
        <h2 id="review-title" class="mt-2 text-2xl font-bold">How did it go?</h2>
        <p class="mt-2 text-sm text-blue-100">Your feedback helps other drivers find great local mechanics.</p>
      </div>
      <form class="space-y-5 p-6 sm:p-8" @submit.prevent="submitReview">
        <fieldset><legend class="text-sm font-semibold text-slate-800">Rate your experience</legend><div class="mt-2 flex gap-2" role="radiogroup" aria-label="Rating">
          <button v-for="star in 5" :key="star" type="button" :aria-label="`${star} star${star === 1 ? '' : 's'}`" :aria-pressed="rating === star" class="text-3xl transition hover:scale-125 focus:outline-none focus:ring-2 focus:ring-blue-400" :class="star <= rating ? 'text-amber-400' : 'text-slate-200'" @click="rating = star">★</button>
        </div></fieldset>
        <label class="block text-sm font-semibold text-slate-800">Your review<textarea v-model="comment" required minlength="1" maxlength="1000" rows="4" placeholder="Tell us about the service…" class="mt-2 w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 font-normal outline-none transition focus:border-blue-400 focus:bg-white focus:ring-4 focus:ring-blue-50"></textarea></label>
        <p v-if="error" role="alert" class="rounded-xl bg-rose-50 px-3 py-2 text-sm text-rose-700">{{ error }}</p>
        <div class="flex justify-end gap-3"><button type="button" class="rounded-xl px-4 py-2.5 text-sm font-semibold text-slate-500 hover:bg-slate-100" @click="$emit('close')">Later</button><button type="submit" :disabled="submitting || !comment.trim()" class="rounded-xl bg-blue-600 px-5 py-2.5 text-sm font-bold text-white shadow-lg shadow-blue-600/20 transition hover:-translate-y-0.5 hover:bg-blue-700 disabled:opacity-50">{{ submitting ? 'Sending…' : 'Send review' }}</button></div>
      </form>
    </section>
  </div>
</template>
