<script setup>
import { API_ORIGIN } from '@/api/http.js'

defineProps({
  mechanic: { type: Object, required: true },
  profile: { type: Object, default: null },
  loading: { type: Boolean, default: false },
  error: { type: String, default: '' },
})

defineEmits(['close'])

function formatPrice(value) {
  return new Intl.NumberFormat('en-PK', { maximumFractionDigits: 2 }).format(Number(value) || 0)
}

function headerStyle(profile) {
  if (!profile?.workshop_image_url) return {}
  const imageUrl = new URL(profile.workshop_image_url, API_ORIGIN).href
  return {
    backgroundImage: `linear-gradient(110deg, rgba(49, 46, 129, .86), rgba(15, 23, 42, .9)), url("${imageUrl}")`,
    backgroundPosition: 'center',
    backgroundSize: 'cover',
  }
}
</script>

<template>
  <div class="fixed inset-0 z-[70] grid place-items-center bg-slate-950/60 p-4 backdrop-blur-sm"
    role="presentation" @click.self="$emit('close')" @keydown.esc="$emit('close')">
    <section role="dialog" aria-modal="true" aria-labelledby="mechanic-profile-title"
      class="max-h-[90vh] w-full max-w-xl overflow-y-auto rounded-3xl border border-white/40 bg-white shadow-2xl shadow-slate-950/30">
      <div class="bg-gradient-to-br from-blue-700 via-indigo-700 to-slate-900 p-6 text-white sm:p-8"
        :style="headerStyle(profile)">
        <div class="flex items-start justify-between gap-4">
          <div class="min-w-0">
            <p class="text-xs font-bold uppercase tracking-[.2em] text-blue-200">Mechanic profile</p>
            <h2 id="mechanic-profile-title" class="mt-2 break-words text-2xl font-bold">
              {{ profile?.shop_name || mechanic.shop_name }}
            </h2>
          </div>
          <button type="button" aria-label="Close mechanic profile"
            class="grid size-9 shrink-0 place-items-center rounded-full bg-white/10 text-xl transition hover:bg-white/20 focus:outline-none focus-visible:ring-2 focus-visible:ring-white"
            @click="$emit('close')">×</button>
        </div>
        <div class="mt-4 flex flex-wrap items-center gap-2 text-xs font-semibold">
          <span v-if="profile?.is_verified ?? mechanic.is_verified" class="rounded-full bg-emerald-300/20 px-3 py-1 text-emerald-100">Verified</span>
          <span v-else class="rounded-full bg-amber-300/20 px-3 py-1 text-amber-100">Verification pending</span>
          <span :class="(profile?.is_online ?? mechanic.is_online) ? 'text-emerald-200' : 'text-slate-300'">
            {{ (profile?.is_online ?? mechanic.is_online) ? 'Online' : 'Offline' }}
          </span>
        </div>
      </div>

      <div class="space-y-6 p-6 sm:p-8">
        <div class="grid gap-4 sm:grid-cols-2">
          <div>
            <p class="text-xs font-bold uppercase tracking-wider text-slate-400">Address</p>
            <p class="mt-1 text-sm leading-6 text-slate-700">{{ profile?.address || mechanic.address || 'Address not provided' }}</p>
            <p v-if="profile?.city || mechanic.city" class="mt-1 text-sm font-semibold text-slate-700">{{ profile?.city || mechanic.city }}</p>
          </div>
          <div>
            <p class="text-xs font-bold uppercase tracking-wider text-slate-400">Customer rating</p>
            <p class="mt-1 text-sm font-semibold text-slate-700">
              <span class="text-amber-500" aria-hidden="true">★</span>
              {{ Number(profile?.average_rating ?? mechanic.average_rating ?? 0).toFixed(1) }} / 5
            </p>
          </div>
        </div>

        <div class="border-t border-slate-100 pt-5">
          <div>
            <p class="text-xs font-bold uppercase tracking-wider text-blue-700">Services</p>
            <h3 class="mt-1 text-lg font-bold text-slate-900">What this shop offers</h3>
          </div>

          <p v-if="loading" role="status" class="mt-4 rounded-xl bg-slate-50 p-4 text-sm text-slate-600">
            Loading profile and services...
          </p>
          <p v-else-if="error" role="alert" class="mt-4 rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">
            {{ error }}
          </p>
          <p v-else-if="!profile?.services?.length" class="mt-4 rounded-xl bg-slate-50 p-4 text-sm text-slate-600">
            This mechanic has not listed any services yet.
          </p>
          <ul v-else class="mt-4 divide-y divide-slate-100 rounded-2xl border border-slate-200">
            <li v-for="service in profile.services" :key="service.id" class="flex flex-wrap items-center justify-between gap-3 p-4">
              <div>
                <p class="font-semibold text-slate-900">{{ service.service_name || 'Service' }}</p>
                <p v-if="service.service_category" class="mt-1 text-xs text-slate-500">{{ service.service_category }}</p>
              </div>
              <p class="text-sm font-semibold text-slate-700">Base price: Rs. {{ formatPrice(service.base_price) }}</p>
            </li>
          </ul>
          <p v-if="profile?.services?.length" class="mt-2 text-xs text-slate-500">Prices are base estimates; final cost may vary by vehicle and repair.</p>
        </div>

        <div class="flex justify-end border-t border-slate-100 pt-4">
          <button type="button" class="rounded-xl bg-blue-700 px-5 py-2.5 text-sm font-bold text-white transition hover:bg-blue-800 focus:outline-none focus-visible:ring-4 focus-visible:ring-blue-200" @click="$emit('close')">
            Done
          </button>
        </div>
      </div>
    </section>
  </div>
</template>
