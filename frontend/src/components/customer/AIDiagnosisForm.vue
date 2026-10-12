<script setup>
import { computed } from 'vue'
import PrimaryButton from '@/components/ui/PrimaryButton.vue'
import StatusBadge from '@/components/ui/StatusBadge.vue'

const description = defineModel('description', { type: String, default: '' })
const images = defineModel('images', { type: Array, default: () => [] })

defineProps({
  diagnosis: { type: Object, default: null },
  request: { type: Object, default: null },
  loading: { type: Boolean, default: false },
})

defineEmits(['search'])

const canSearch = computed(() => description.value.trim().length >= 10)

function selectImages(event) {
  images.value = Array.from(event.target.files || [])
}

function clearImages() {
  images.value = []
}

function faultsList(faults) {
  if (!faults) return []
  if (Array.isArray(faults)) return faults.map((fault, index) => ({ key: `fault-${index}`, label: '', value: fault }))
  if (typeof faults === 'object') return Object.entries(faults).map(([label, value]) => ({ key: label, label, value }))
  return [{ key: 'fault', label: '', value: faults }]
}

</script>

<template>
  <section class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
    <div class="flex items-start gap-4">
      <span class="grid size-11 shrink-0 place-items-center rounded-xl bg-blue-50 text-xl text-blue-700" aria-hidden="true">✦</span>
      <div>
        <p class="text-sm font-semibold uppercase tracking-wider text-blue-600">Start a repair request</p>
        <h2 class="mt-1 text-xl font-bold">Describe your car problem</h2>
        <p class="mt-1 text-sm leading-6 text-slate-600">Share the symptoms so nearby mechanics can understand what you need.</p>
      </div>
    </div>

    <form class="mt-6 space-y-5" @submit.prevent="$emit('search')">
      <div>
        <label for="problem-description" class="mb-2 block text-sm font-medium text-slate-700">What’s going on?</label>
        <textarea id="problem-description" v-model="description" rows="5" minlength="10" maxlength="2000" required
          placeholder="For example: I hear a clicking sound when I turn the key…"
          class="w-full resize-y rounded-lg border border-slate-300 px-3.5 py-3 text-slate-900 outline-none placeholder:text-slate-400 focus:border-blue-500 focus:ring-4 focus:ring-blue-100"></textarea>
        <p class="mt-1 text-right text-xs text-slate-500">{{ description.length }}/2000</p>
      </div>

      <div>
        <label for="problem-images" class="mb-2 block text-sm font-medium text-slate-700">Photos <span class="font-normal text-slate-500">(optional)</span></label>
        <input id="problem-images" type="file" accept="image/*" multiple @change="selectImages"
          class="block w-full rounded-lg border border-slate-300 bg-white text-sm text-slate-600 file:mr-4 file:border-0 file:bg-slate-100 file:px-4 file:py-3 file:font-semibold file:text-slate-700 hover:file:bg-slate-200" />
        <div v-if="images.length" class="mt-2 flex flex-wrap items-center gap-2 text-sm text-slate-600">
          <span>{{ images.length }} photo(s) selected</span>
          <button type="button" class="font-semibold text-blue-700 hover:text-blue-800" @click="clearImages">Clear</button>
        </div>
        <p class="mt-1 text-xs leading-5 text-slate-500">Photos are selected locally; the current repair API accepts text and location only.</p>
      </div>

      <PrimaryButton type="submit" :loading="loading" :disabled="!canSearch" class="w-full sm:w-auto">
        {{ loading ? 'Finding mechanics...' : 'Find nearby mechanics' }}
      </PrimaryButton>
    </form>

    <div v-if="request" class="mt-6 rounded-xl border border-emerald-200 bg-emerald-50 p-4">
      <div class="flex flex-wrap items-center justify-between gap-2">
        <p class="font-semibold text-emerald-950">Repair request created</p>
        <StatusBadge :status="request.status" />
      </div>
      <p class="mt-1 text-sm text-emerald-900">Request #{{ request.id.slice(0, 8) }} is now in your request history.</p>
    </div>

    <div v-if="diagnosis" class="mt-6 rounded-xl border border-blue-200 bg-blue-50/70 p-5">
      <div class="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p class="text-sm font-semibold uppercase tracking-wider text-blue-700">AI diagnosis</p>
          <h3 class="mt-1 text-lg font-bold text-slate-900">Initial assessment</h3>
        </div>
        <StatusBadge :status="diagnosis.urgency" :label="`${diagnosis.urgency} urgency`" />
      </div>
      <p class="mt-3 text-sm leading-6 text-slate-700">{{ diagnosis.ai_summary }}</p>
      <div v-if="faultsList(diagnosis.possible_faults).length" class="mt-4">
        <h4 class="text-sm font-bold text-slate-800">Possible faults</h4>
        <ul class="mt-2 space-y-2">
          <li v-for="fault in faultsList(diagnosis.possible_faults)" :key="fault.key" class="rounded-lg bg-white/80 px-3 py-2 text-sm text-slate-700">
            <span v-if="fault.label" class="font-semibold">{{ fault.label }}: </span>{{ typeof fault.value === 'object' ? JSON.stringify(fault.value) : fault.value }}
          </li>
        </ul>
      </div>
    </div>
    <div v-else-if="request" class="mt-4 rounded-xl border border-slate-200 bg-slate-50 p-4 text-sm leading-6 text-slate-600">
      The current backend did not return an AI diagnosis for this request. Your repair request was still sent successfully.
    </div>
  </section>
</template>
