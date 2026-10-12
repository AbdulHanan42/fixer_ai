<script setup>
import { reactive, ref } from 'vue'

defineProps({
  vehicles: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
  saving: { type: Boolean, default: false },
  error: { type: String, default: '' },
})

const emit = defineEmits(['create', 'remove'])
const selectedVehicleId = defineModel('selectedVehicleId', { type: String, default: '' })
const showForm = ref(false)
const form = reactive({ make: '', model: '', year: new Date().getFullYear() })

function submit() {
  emit('create', { make: form.make.trim(), model: form.model.trim(), year: Number(form.year) })
}

function reset() {
  form.make = ''
  form.model = ''
  form.year = new Date().getFullYear()
  showForm.value = false
}
</script>

<template>
  <section class="rounded-2xl border border-slate-200/80 bg-white/90 p-5 shadow-sm sm:p-6">
    <div class="flex flex-wrap items-start justify-between gap-4">
      <div><p class="text-[11px] font-bold uppercase tracking-[.2em] text-blue-700">Your garage</p><h2 class="mt-1 text-lg font-bold text-slate-900">Choose a vehicle</h2><p class="mt-1 text-sm text-slate-500">Attach your car to a repair request for better context.</p></div>
      <button type="button" class="rounded-xl border border-slate-200 px-3 py-2 text-xs font-bold text-slate-700 transition hover:border-blue-200 hover:bg-blue-50 hover:text-blue-700" @click="showForm = !showForm">{{ showForm ? 'Cancel' : '＋ Add vehicle' }}</button>
    </div>
    <p v-if="error" role="alert" class="mt-4 rounded-xl bg-rose-50 px-3 py-2 text-sm text-rose-700">{{ error }}</p>
    <div v-if="loading" class="mt-4 animate-pulse rounded-xl bg-slate-100 p-4 text-sm text-slate-500" role="status">Loading your garage…</div>
    <div v-else-if="vehicles.length" class="mt-4 grid gap-2 sm:grid-cols-2">
      <label v-for="vehicle in vehicles" :key="vehicle.id" class="flex cursor-pointer items-center gap-3 rounded-xl border p-3 transition" :class="selectedVehicleId === vehicle.id ? 'border-blue-400 bg-blue-50 ring-2 ring-blue-100' : 'border-slate-200 hover:border-slate-300'">
        <input v-model="selectedVehicleId" type="radio" name="selected-vehicle" :value="vehicle.id" class="size-4 accent-blue-600" />
        <span class="min-w-0 flex-1"><span class="block truncate text-sm font-bold text-slate-800">{{ vehicle.year }} {{ vehicle.make }} {{ vehicle.model }}</span><span class="mt-0.5 block text-[11px] text-slate-500">Select for your next repair</span></span>
        <button type="button" class="rounded-lg p-2 text-xs font-semibold text-slate-400 hover:bg-rose-50 hover:text-rose-600" :aria-label="`Remove ${vehicle.year} ${vehicle.make} ${vehicle.model}`" @click.stop.prevent="emit('remove', vehicle)">Remove</button>
      </label>
      <button type="button" class="rounded-xl border border-dashed border-slate-300 p-3 text-left text-sm text-slate-500 transition hover:border-blue-300 hover:text-blue-700" :class="!selectedVehicleId ? 'border-blue-300 bg-blue-50/50 text-blue-800' : ''" @click="selectedVehicleId = ''">No specific vehicle</button>
    </div>
    <p v-else-if="!loading" class="mt-4 rounded-xl border border-dashed border-slate-300 bg-slate-50 p-4 text-sm text-slate-600">No vehicles yet. You can add one or continue without a vehicle.</p>

    <form v-if="showForm" class="mt-4 grid gap-3 rounded-xl bg-slate-50 p-4 sm:grid-cols-3" @submit.prevent="submit">
      <label class="text-xs font-semibold text-slate-600">Make<input v-model.trim="form.make" required minlength="2" maxlength="50" placeholder="Toyota" class="mt-1.5 w-full rounded-lg border border-slate-200 bg-white px-3 py-2.5 text-sm text-slate-900 outline-none focus:border-blue-400 focus:ring-4 focus:ring-blue-50" /></label>
      <label class="text-xs font-semibold text-slate-600">Model<input v-model.trim="form.model" required minlength="2" maxlength="50" placeholder="Corolla" class="mt-1.5 w-full rounded-lg border border-slate-200 bg-white px-3 py-2.5 text-sm text-slate-900 outline-none focus:border-blue-400 focus:ring-4 focus:ring-blue-50" /></label>
      <label class="text-xs font-semibold text-slate-600">Year<input v-model.number="form.year" type="number" min="1900" max="2100" required class="mt-1.5 w-full rounded-lg border border-slate-200 bg-white px-3 py-2.5 text-sm text-slate-900 outline-none focus:border-blue-400 focus:ring-4 focus:ring-blue-50" /></label>
      <div class="flex justify-end gap-2 sm:col-span-3"><button type="button" class="rounded-lg px-3 py-2 text-sm font-semibold text-slate-600 hover:bg-white" @click="reset">Cancel</button><button type="submit" :disabled="saving" class="rounded-lg bg-slate-950 px-4 py-2 text-sm font-bold text-white transition hover:bg-blue-700 disabled:opacity-50">{{ saving ? 'Saving…' : 'Save vehicle' }}</button></div>
    </form>
  </section>
</template>
