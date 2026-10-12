<script setup>
import { computed } from 'vue'
import PrimaryButton from '@/components/ui/PrimaryButton.vue'
import StatusBadge from '@/components/ui/StatusBadge.vue'
import { locationService } from '@/services/location.service.js'

const props = defineProps({
  location: { type: Object, default: null },
  mechanics: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
  error: { type: String, default: '' },
  busyMechanicId: { type: String, default: '' },
  canRequest: { type: Boolean, default: false },
})

defineEmits(['request-repair', 'retry'])

const nearbyMechanics = computed(() => {
  if (!props.location) return props.mechanics
  return props.mechanics
    .map((mechanic) => ({
      ...mechanic,
      distanceKm:
        mechanic.latitude == null || mechanic.longitude == null
          ? null
          : locationService.calculateDistance(
              props.location.latitude,
              props.location.longitude,
              mechanic.latitude,
              mechanic.longitude,
            ),
    }))
    .sort((a, b) => (a.distanceKm ?? Infinity) - (b.distanceKm ?? Infinity))
})
</script>

<template>
  <section class="space-y-5">
    <div class="flex flex-wrap items-end justify-between gap-3">
      <div>
        <p class="text-sm font-semibold uppercase tracking-wider text-blue-600">Local repair network</p>
        <h2 class="mt-1 text-2xl font-bold tracking-tight text-slate-900">Nearby mechanics</h2>
        <p class="mt-1 text-sm text-slate-600">Mechanics are ordered by distance when location details are available.</p>
      </div>
      <span v-if="mechanics.length" class="rounded-full bg-blue-50 px-3 py-1 text-sm font-semibold text-blue-800">{{ mechanics.length }} found</span>
    </div>

    <div v-if="location" class="relative overflow-hidden rounded-2xl border border-slate-200 bg-gradient-to-br from-sky-50 via-emerald-50 to-slate-100 p-5 shadow-sm">
      <div class="absolute inset-0 opacity-50" aria-hidden="true">
        <div class="absolute left-1/4 top-0 h-full w-px rotate-12 bg-white"></div>
        <div class="absolute left-2/3 top-0 h-full w-px -rotate-12 bg-white"></div>
        <div class="absolute left-0 top-1/3 h-px w-full rotate-3 bg-white"></div>
        <div class="absolute left-0 top-2/3 h-px w-full -rotate-3 bg-white"></div>
      </div>
      <div class="relative flex min-h-36 flex-col justify-between gap-4 sm:flex-row sm:items-center">
        <div>
          <p class="text-sm font-semibold text-slate-800">Map preview</p>
          <p class="mt-1 text-xs text-slate-600">Showing your search area and {{ mechanics.length }} mechanic result(s)</p>
          <p class="mt-2 font-mono text-xs text-slate-500">{{ location.latitude.toFixed(4) }}, {{ location.longitude.toFixed(4) }}</p>
        </div>
        <div class="flex flex-wrap items-center gap-3">
          <span class="inline-flex items-center gap-2 rounded-full bg-white/90 px-3 py-2 text-xs font-semibold text-slate-700 shadow-sm">
            <span class="size-2.5 rounded-full bg-blue-600 ring-4 ring-blue-200"></span>You
          </span>
          <span v-for="mechanic in nearbyMechanics.slice(0, 5)" :key="mechanic.id"
            class="inline-flex items-center gap-2 rounded-full bg-white/90 px-3 py-2 text-xs font-semibold text-slate-700 shadow-sm">
            <span class="size-2.5 rounded-full bg-amber-500"></span>{{ mechanic.shop_name }}
          </span>
        </div>
      </div>
    </div>

    <p v-if="error" role="alert" class="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-800">{{ error }}</p>

    <div v-if="loading" class="grid min-h-40 place-items-center rounded-2xl border border-slate-200 bg-white p-8 text-sm text-slate-600" role="status">
      Searching nearby mechanics...
    </div>
    <div v-else-if="!location && !error" class="rounded-2xl border border-dashed border-slate-300 bg-white p-8 text-center">
      <p class="font-semibold text-slate-800">Share your location to search nearby</p>
      <p class="mt-1 text-sm text-slate-500">Your coordinates are used to find mechanics within 50 km.</p>
    </div>
    <div v-else-if="location && !nearbyMechanics.length && !error" class="rounded-2xl border border-slate-200 bg-white p-8 text-center">
      <p class="font-semibold text-slate-800">No mechanics found nearby</p>
      <p class="mt-1 text-sm text-slate-500">Try searching again later or adjust your location.</p>
      <button type="button" class="mt-4 text-sm font-semibold text-blue-700 hover:text-blue-800" @click="$emit('retry')">Search again</button>
    </div>

    <div v-else-if="!loading && location && nearbyMechanics.length" class="grid gap-4 md:grid-cols-2">
      <article v-for="mechanic in nearbyMechanics" :key="mechanic.id"
        class="flex flex-col rounded-2xl border border-slate-200 bg-white p-5 shadow-sm transition hover:border-blue-200 hover:shadow-md">
        <div class="flex items-start justify-between gap-3">
          <div class="min-w-0">
            <h3 class="truncate text-lg font-bold text-slate-900">{{ mechanic.shop_name }}</h3>
            <p class="mt-1 text-sm leading-5 text-slate-600">{{ mechanic.address }}</p>
          </div>
          <StatusBadge v-if="mechanic.is_verified" status="available" label="Verified" />
        </div>
        <div class="mt-4 flex flex-wrap items-center gap-x-4 gap-y-2 text-sm text-slate-600">
          <span class="inline-flex items-center gap-1.5"><span class="text-amber-500" aria-hidden="true">★</span>{{ Number(mechanic.average_rating || 0).toFixed(1) }} rating</span>
          <span v-if="mechanic.distanceKm != null">{{ mechanic.distanceKm.toFixed(1) }} km away</span>
          <span v-else>Distance unavailable</span>
        </div>
        <div class="mt-5 border-t border-slate-100 pt-4">
          <PrimaryButton class="w-full" :loading="busyMechanicId === mechanic.id"
            :disabled="!canRequest || Boolean(busyMechanicId)" @click="$emit('request-repair', mechanic)">
            {{ busyMechanicId === mechanic.id ? 'Sending request...' : 'Request repair' }}
          </PrimaryButton>
        </div>
      </article>
    </div>
  </section>
</template>
