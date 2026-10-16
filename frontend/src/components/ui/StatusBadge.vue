<script setup>
import { computed } from 'vue'

const props = defineProps({
  status: { type: String, required: true },
  label: { type: String, default: '' },
})

const styles = {
  online: 'bg-emerald-50 text-emerald-700 ring-emerald-600/20',
  available: 'bg-emerald-50 text-emerald-700 ring-emerald-600/20',
  completed: 'bg-emerald-50 text-emerald-700 ring-emerald-600/20',
  pending: 'bg-amber-50 text-amber-800 ring-amber-600/20',
  accepted: 'bg-blue-50 text-blue-700 ring-blue-600/20',
  in_progress: 'bg-blue-50 text-blue-700 ring-blue-600/20',
  offline: 'bg-slate-100 text-slate-600 ring-slate-500/20',
  cancelled: 'bg-red-50 text-red-700 ring-red-600/20',
  critical: 'bg-red-50 text-red-700 ring-red-600/20',
  high: 'bg-red-50 text-red-700 ring-red-600/20',
  urgent: 'bg-red-50 text-red-700 ring-red-600/20',
  medium: 'bg-amber-50 text-amber-800 ring-amber-600/20',
  low: 'bg-emerald-50 text-emerald-700 ring-emerald-600/20',
}

const badgeClass = computed(() => styles[props.status.toLowerCase()] || styles.offline)
const displayLabel = computed(() => props.label || props.status.replaceAll('_', ' '))
</script>

<template>
  <span class="inline-flex items-center rounded-full px-2.5 py-1 text-xs font-semibold capitalize ring-1 ring-inset" :class="badgeClass">
    {{ displayLabel }}
  </span>
</template>
