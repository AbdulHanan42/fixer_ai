<script setup>
import { computed } from 'vue'
import PrimaryButton from '@/components/ui/PrimaryButton.vue'
import StatusBadge from '@/components/ui/StatusBadge.vue'
import { locationService } from '@/services/location.service.js'

const props = defineProps({
  location: { type: Object, default: null },
  mechanics: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
  searched: { type: Boolean, default: false },
  city: { type: String, default: '' },
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

const mapUrl = computed(() => {
  if (!props.location) return ''
  const { latitude, longitude } = props.location
  const bbox = [longitude - 0.035, latitude - 0.02, longitude + 0.035, latitude + 0.02].join(',')
  const query = new URLSearchParams({ bbox, layer: 'mapnik', marker: `${latitude},${longitude}` })
  return `https://www.openstreetmap.org/export/embed.html?${query}`
})

const externalMapUrl = computed(() => props.location
  ? `https://www.openstreetmap.org/?mlat=${props.location.latitude}&mlon=${props.location.longitude}#map=13/${props.location.latitude}/${props.location.longitude}`
  : '')
</script>

<template>
  <section class="space-y-5">
    <div class="flex flex-wrap items-end justify-between gap-3">
      <div>
        <p class="text-sm font-semibold uppercase tracking-wider text-blue-600">Local repair network</p>
        <h2 class="mt-1 text-2xl font-bold tracking-tight text-slate-900">{{ city ? `Mechanics in ${city}` : location ? 'Nearby mechanics' : 'Registered mechanic profiles' }}</h2>
        <p class="mt-1 text-sm text-slate-600">{{ location ? 'Verified, available shops are prioritized; issue matches and distance help order the rest.' : 'Browse registered shops; profile verification and availability are shown on each card.' }}</p>
      </div>
      <span v-if="mechanics.length" class="rounded-full bg-blue-50 px-3 py-1 text-sm font-semibold text-blue-800">{{ mechanics.length }} found</span>
    </div>

    <div v-if="location" class="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
      <iframe :src="mapUrl" title="OpenStreetMap showing your current location" loading="lazy" referrerpolicy="no-referrer" class="h-64 w-full border-0 sm:h-72"></iframe>
      <div class="flex flex-wrap items-center justify-between gap-3 border-t border-slate-100 px-4 py-3">
        <p class="text-xs text-slate-500">Map centered at <span class="font-mono text-slate-700">{{ location.latitude.toFixed(4) }}, {{ location.longitude.toFixed(4) }}</span></p>
        <a :href="externalMapUrl" target="_blank" rel="noreferrer" class="text-xs font-bold text-blue-700 hover:text-blue-900">Open full map <span aria-hidden="true">↗</span></a>
      </div>
    </div>

    <p v-if="error" role="alert" class="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-800">{{ error }}</p>

    <div v-if="loading" class="grid min-h-40 place-items-center rounded-2xl border border-slate-200 bg-white p-8 text-sm text-slate-600" role="status">
      Searching mechanic profiles...
    </div>
    <div v-else-if="!searched && !location && !error" class="rounded-2xl border border-dashed border-slate-300 bg-white p-8 text-center">
      <p class="font-semibold text-slate-800">Share your location to search nearby</p>
      <p class="mt-1 text-sm text-slate-500">Or use the city filter below to browse registered shops.</p>
    </div>
    <div v-else-if="searched && !nearbyMechanics.length && !error" class="rounded-2xl border border-slate-200 bg-white p-8 text-center">
      <p class="font-semibold text-slate-800">No mechanic profiles found{{ city ? ` in ${city}` : location ? ' nearby' : '' }}</p>
      <p class="mt-1 text-sm text-slate-500">Try another city or check back as more shops join Fixer AI.</p>
      <button type="button" class="mt-4 text-sm font-semibold text-blue-700 hover:text-blue-800" @click="$emit('retry')">Search again</button>
    </div>

    <div v-else-if="!loading && nearbyMechanics.length" class="grid gap-4 md:grid-cols-2">
      <article v-for="mechanic in nearbyMechanics" :key="mechanic.id"
        class="flex flex-col rounded-2xl border border-slate-200 bg-white p-5 shadow-sm transition hover:border-blue-200 hover:shadow-md">
        <div class="flex items-start justify-between gap-3">
          <div class="min-w-0">
            <h3 class="truncate text-lg font-bold text-slate-900">{{ mechanic.shop_name }}</h3>
            <p class="mt-1 text-sm leading-5 text-slate-600">{{ mechanic.address }}</p>
            <p v-if="mechanic.city" class="mt-1 text-sm font-semibold text-slate-700">{{ mechanic.city }}</p>
          </div>
          <div class="flex shrink-0 flex-col items-end gap-1.5">
            <StatusBadge v-if="mechanic.is_verified" status="available" label="Verified" />
            <StatusBadge v-else status="pending" label="Verification pending" />
            <span v-if="mechanic.issue_match" class="rounded-full bg-blue-50 px-2.5 py-1 text-[11px] font-bold text-blue-700">Issue match</span>
          </div>
        </div>
        <div class="mt-4 flex flex-wrap items-center gap-x-4 gap-y-2 text-sm text-slate-600">
          <span class="inline-flex items-center gap-1.5"><span class="text-amber-500" aria-hidden="true">★</span>{{ Number(mechanic.average_rating || 0).toFixed(1) }} rating</span>
          <span v-if="mechanic.distanceKm != null">{{ mechanic.distanceKm.toFixed(1) }} km away</span>
          <span v-else-if="!location">City search · distance not shared</span>
          <span v-else>Distance unavailable</span>
          <span :class="mechanic.is_online ? 'text-emerald-700' : 'text-slate-500'">{{ mechanic.is_online ? 'Online' : 'Offline' }}</span>
        </div>
        <div class="mt-5 border-t border-slate-100 pt-4">
          <PrimaryButton class="w-full" :loading="busyMechanicId === mechanic.id"
            :disabled="!canRequest || !mechanic.is_verified || !mechanic.is_online || Boolean(busyMechanicId)" @click="$emit('request-repair', mechanic)">
            {{ busyMechanicId === mechanic.id ? 'Sending request...' : !mechanic.is_verified ? 'Awaiting verification' : mechanic.is_online ? 'Request repair' : 'Currently offline' }}
          </PrimaryButton>
        </div>
      </article>
    </div>
  </section>
</template>
