<script setup>
import { onMounted, ref } from 'vue'
import { adminService } from '@/services/admin.service.js'
import { useNotifications } from '@/composables/useNotifications.js'

const { showError, showSuccess } = useNotifications()
const pendingMechanics = ref([])
const loading = ref(true)
const refreshing = ref(false)
const busyId = ref('')
const pageError = ref('')

async function loadPending({ silent = false } = {}) {
  if (silent) refreshing.value = true
  else loading.value = true
  pageError.value = ''
  try {
    pendingMechanics.value = await adminService.getPendingMechanics()
  } catch (error) {
    pageError.value = error.message || 'Could not load mechanic verification requests.'
  } finally {
    loading.value = false
    refreshing.value = false
  }
}

async function verify(mechanic) {
  busyId.value = mechanic.id
  try {
    await adminService.verifyMechanic(mechanic.id)
    pendingMechanics.value = pendingMechanics.value.filter((item) => item.id !== mechanic.id)
    showSuccess(`${mechanic.shop_name} is now verified.`)
  } catch (error) {
    showError(error.message || 'Could not verify this shop.')
  } finally {
    busyId.value = ''
  }
}

onMounted(loadPending)
</script>

<template>
  <div class="space-y-8">
    <section class="flex flex-col justify-between gap-5 rounded-3xl bg-gradient-to-br from-slate-950 via-slate-900 to-indigo-950 p-6 text-white shadow-xl shadow-indigo-950/15 sm:p-8 lg:flex-row lg:items-end">
      <div><p class="text-xs font-bold uppercase tracking-[.22em] text-blue-300">Platform operations</p><h1 class="mt-2 text-3xl font-bold tracking-tight sm:text-4xl">Trust & verification</h1><p class="mt-3 max-w-xl text-sm leading-6 text-slate-300">Review shop details before mechanics appear as verified in customer search.</p></div>
      <button type="button" :disabled="refreshing" class="rounded-xl border border-white/15 bg-white/10 px-4 py-2.5 text-sm font-bold text-white transition hover:bg-white/15 disabled:opacity-50" @click="loadPending({ silent: true })">{{ refreshing ? 'Refreshing...' : 'Refresh list' }}</button>
    </section>

    <p v-if="pageError" role="alert" class="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800">{{ pageError }}</p>

    <section class="grid gap-4 sm:grid-cols-3">
      <article class="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"><p class="text-xs font-bold uppercase tracking-wider text-slate-500">Waiting review</p><p class="mt-2 text-3xl font-black text-slate-900">{{ pendingMechanics.length }}</p><p class="mt-1 text-xs text-slate-500">Mechanic shops pending verification</p></article>
      <article class="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"><p class="text-xs font-bold uppercase tracking-wider text-slate-500">Review standard</p><p class="mt-2 text-lg font-bold text-slate-900">Shop details</p><p class="mt-1 text-xs text-slate-500">Confirm the listed name, contact and address.</p></article>
      <article class="rounded-2xl border border-blue-100 bg-blue-50/70 p-5"><p class="text-xs font-bold uppercase tracking-wider text-blue-700">Customer trust</p><p class="mt-2 text-lg font-bold text-slate-900">Verified listings</p><p class="mt-1 text-xs leading-5 text-slate-600">Approved shops receive a verified badge in nearby search.</p></article>
    </section>

    <section class="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm">
      <header class="border-b border-slate-100 px-5 py-4 sm:px-6"><h2 class="font-bold text-slate-900">Pending mechanic profiles</h2><p class="mt-1 text-xs text-slate-500">Verify only when the shop information is ready to publish.</p></header>
      <div v-if="loading" class="grid min-h-48 place-items-center text-sm text-slate-500" role="status">Loading verification requests...</div>
      <div v-else-if="!pendingMechanics.length" class="grid min-h-64 place-items-center p-8 text-center"><div><span class="mx-auto grid size-14 place-items-center rounded-2xl bg-emerald-50 text-2xl text-emerald-700">✓</span><h3 class="mt-4 font-bold text-slate-900">All caught up</h3><p class="mt-1 max-w-sm text-sm leading-6 text-slate-500">There are no shop profiles waiting for verification right now.</p></div></div>
      <div v-else class="divide-y divide-slate-100">
        <article v-for="mechanic in pendingMechanics" :key="mechanic.id" class="flex flex-col gap-5 p-5 transition hover:bg-slate-50/70 sm:p-6 lg:flex-row lg:items-center lg:justify-between">
          <div class="flex min-w-0 items-start gap-4">
            <div class="grid size-12 shrink-0 place-items-center rounded-2xl bg-gradient-to-br from-blue-100 to-indigo-100 text-lg font-black text-blue-800">{{ (mechanic.mechanic_name || mechanic.shop_name).slice(0, 1).toUpperCase() }}</div>
            <div class="min-w-0"><div class="flex flex-wrap items-center gap-2"><h3 class="text-base font-bold text-slate-900">{{ mechanic.shop_name }}</h3><span class="rounded-full bg-amber-50 px-2.5 py-1 text-[10px] font-bold uppercase tracking-wide text-amber-800">Pending</span></div><p class="mt-1 text-sm text-slate-600">{{ mechanic.mechanic_name || 'Mechanic name unavailable' }}</p><p class="mt-1 break-all text-xs text-slate-500">{{ mechanic.mechanic_email || 'No email' }}<span v-if="mechanic.mechanic_phone"> · {{ mechanic.mechanic_phone }}</span></p><p class="mt-2 text-sm text-slate-500">{{ mechanic.address }}<span v-if="mechanic.city">, {{ mechanic.city }}</span></p><p v-if="mechanic.latitude != null && mechanic.longitude != null" class="mt-1 font-mono text-[11px] text-slate-400">{{ Number(mechanic.latitude).toFixed(4) }}, {{ Number(mechanic.longitude).toFixed(4) }}</p></div>
          </div>
          <button type="button" :disabled="Boolean(busyId)" class="w-full rounded-xl bg-emerald-600 px-5 py-3 text-sm font-bold text-white shadow-lg shadow-emerald-600/15 transition hover:-translate-y-0.5 hover:bg-emerald-700 disabled:opacity-50 lg:w-auto" @click="verify(mechanic)">{{ busyId === mechanic.id ? 'Verifying...' : 'Approve shop' }}</button>
        </article>
      </div>
    </section>
  </div>
</template>
