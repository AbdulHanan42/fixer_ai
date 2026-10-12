<script setup>
import { onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import AIDiagnosisForm from '@/components/customer/AIDiagnosisForm.vue'
import MechanicList from '@/components/customer/MechanicList.vue'
import VehicleGarage from '@/components/customer/VehicleGarage.vue'
import ChatBox from '@/components/chat/ChatBox.vue'
import ReviewModal from '@/components/customer/ReviewModal.vue'
import http from '@/api/http.js'
import { useNotifications } from '@/composables/useNotifications.js'
import { useLocation } from '@/composables/useLocation.js'
import { mechanicService } from '@/services/mechanic.service.js'
import { repairService } from '@/services/repair.service.js'
import { vehicleService } from '@/services/vehicle.service.js'

const { location, error: locationError, isLoading: isLocating, getCurrentLocation } = useLocation()
const { showError, showSuccess } = useNotifications()
const route = useRoute()

const description = ref('')
const mechanics = ref([])
const cityQuery = ref('')
const directorySearched = ref(false)
const vehicles = ref([])
const selectedVehicleId = ref('')
const vehiclesLoading = ref(true)
const vehicleSaving = ref(false)
const vehicleError = ref('')
const searchError = ref('')
const isSearching = ref(false)
const busyMechanicId = ref('')
const latestRequest = ref(null)
const aiDiagnosis = ref(null)
const recentRequests = ref([])
const activeChatRequestId = ref('')
const reviewCandidate = ref(null)
const reviewedIds = new Set()
const dismissedReviewIds = new Set()

watch(() => route.query.chat, (requestId) => {
  activeChatRequestId.value = typeof requestId === 'string' ? requestId : ''
}, { immediate: true })

async function findNearbyMechanics() {
  searchError.value = ''
  cityQuery.value = ''
  isSearching.value = true
  await getCurrentLocation()
  if (!location.value) {
    searchError.value = locationError.value || 'Your location could not be read. Allow location access and try again.'
    isSearching.value = false
    return
  }

  try {
    mechanics.value = await mechanicService.searchMechanics({
      latitude: location.value.latitude,
      longitude: location.value.longitude,
      radius_km: 50,
      issue: description.value.trim(),
    })
    directorySearched.value = true
  } catch (error) {
    searchError.value = error.message || 'Could not load nearby mechanics.'
  } finally {
    isSearching.value = false
  }
}

async function searchMechanicsByCity() {
  const city = cityQuery.value.trim()
  searchError.value = ''
  if (city.length < 2) {
    searchError.value = 'Enter at least two characters for a city name.'
    return
  }
  isSearching.value = true
  directorySearched.value = true
  location.value = null
  try {
      mechanics.value = await mechanicService.searchDirectory(city, description.value.trim())
  } catch (error) {
    mechanics.value = []
    searchError.value = error.message || `Could not find mechanics in ${city}.`
  } finally {
    isSearching.value = false
  }
}

async function browseVerifiedMechanics() {
  searchError.value = ''
  cityQuery.value = ''
  isSearching.value = true
  directorySearched.value = true
  location.value = null
  try {
    mechanics.value = await mechanicService.searchDirectory('', description.value.trim())
  } catch (error) {
    mechanics.value = []
    searchError.value = error.message || 'Could not load mechanic profiles.'
  } finally {
    isSearching.value = false
  }
}

async function requestRepair(mechanic) {
  if (description.value.trim().length < 10) {
    showError('Describe the problem in at least 10 characters before requesting a repair.')
    return
  }

  busyMechanicId.value = mechanic.id
  aiDiagnosis.value = null
  try {
    const repairData = {
      description: description.value.trim(),
      mechanic_id: mechanic.id,
      vehicle_id: selectedVehicleId.value || null,
    }
    if (location.value) {
      repairData.latitude = location.value.latitude
      repairData.longitude = location.value.longitude
    }
    const created = await repairService.createRepairRequest(repairData)
    latestRequest.value = created
    recentRequests.value = [created, ...recentRequests.value]
    showSuccess(`Repair request sent to ${mechanic.shop_name}.`)

    try {
      const details = await repairService.getRepairRequest(created.id)
      latestRequest.value = details
      aiDiagnosis.value = details.ai_diagnosis || null
    } catch {
      // The request itself was created successfully; details can be loaded later.
    }
  } catch (error) {
    showError(error.message || 'Could not send the repair request.')
  } finally {
    busyMechanicId.value = ''
  }
}

async function cancelRepair(request) {
  if (!window.confirm('Cancel this pending repair request?')) return
  busyMechanicId.value = request.id
  try {
    const updated = await repairService.cancelRepairRequest(request.id)
    recentRequests.value = recentRequests.value.map((item) => item.id === updated.id ? updated : item)
    showSuccess('Repair request cancelled.')
  } catch (error) {
    showError(error.message || 'Could not cancel this repair request.')
  } finally {
    busyMechanicId.value = ''
  }
}

async function loadRequestHistory() {
  try {
    recentRequests.value = await repairService.getMyRepairRequests()
    const completed = recentRequests.value.filter((request) => request.status === 'completed' && request.mechanic_id && !reviewedIds.has(request.id) && !dismissedReviewIds.has(request.id))
    for (const request of completed) {
      try {
        const result = await http.get(`/reviews/request/${request.id}/status`)
        if (result.reviewed) reviewedIds.add(request.id)
        else if (!reviewCandidate.value) reviewCandidate.value = request
      } catch {
        // Keep history available even if review status cannot be checked.
      }
    }
  } catch {
    // Dashboard history is secondary to the location-based request flow.
  }
}

async function loadVehicles() {
  vehicleError.value = ''
  vehiclesLoading.value = true
  try {
    vehicles.value = await vehicleService.list()
    if (selectedVehicleId.value && !vehicles.value.some((vehicle) => vehicle.id === selectedVehicleId.value)) selectedVehicleId.value = ''
  } catch (error) {
    vehicleError.value = error.message || 'Could not load your garage.'
  } finally {
    vehiclesLoading.value = false
  }
}

async function createVehicle(vehicle) {
  vehicleSaving.value = true
  vehicleError.value = ''
  try {
    const created = await vehicleService.create(vehicle)
    vehicles.value = [created, ...vehicles.value]
    selectedVehicleId.value = created.id
    showSuccess('Vehicle added to your garage.')
  } catch (error) {
    vehicleError.value = error.message || 'Could not save this vehicle.'
  } finally {
    vehicleSaving.value = false
  }
}

async function removeVehicle(vehicle) {
  if (!window.confirm(`Remove ${vehicle.year} ${vehicle.make} ${vehicle.model} from your garage?`)) return
  vehicleSaving.value = true
  vehicleError.value = ''
  try {
    await vehicleService.remove(vehicle.id)
    vehicles.value = vehicles.value.filter((item) => item.id !== vehicle.id)
    if (selectedVehicleId.value === vehicle.id) selectedVehicleId.value = ''
    showSuccess('Vehicle removed from your garage.')
  } catch (error) {
    vehicleError.value = error.message || 'Could not remove this vehicle.'
  } finally {
    vehicleSaving.value = false
  }
}

function formatCoordinates() {
  return location.value ? `${location.value.latitude.toFixed(4)}, ${location.value.longitude.toFixed(4)}` : ''
}

function dismissReview() {
  if (reviewCandidate.value) dismissedReviewIds.add(reviewCandidate.value.id)
  reviewCandidate.value = null
}

function onReviewSubmitted(requestId) {
  reviewedIds.add(requestId)
  reviewCandidate.value = null
}

let historyRefreshTimer
onMounted(() => {
  loadVehicles()
  loadRequestHistory()
  historyRefreshTimer = window.setInterval(loadRequestHistory, 30000)
})
onUnmounted(() => window.clearInterval(historyRefreshTimer))
</script>

<template>
  <div class="space-y-10">
    <section>
      <p class="text-sm font-semibold uppercase tracking-wider text-blue-600">Customer workspace</p>
      <h1 class="mt-2 text-3xl font-bold tracking-tight sm:text-4xl">Find help for your car</h1>
      <p class="mt-3 max-w-2xl text-slate-600">Describe the issue and browse verified repair shops by city or nearby location.</p>
    </section>

    <VehicleGarage v-model:selected-vehicle-id="selectedVehicleId" :vehicles="vehicles" :loading="vehiclesLoading"
      :saving="vehicleSaving" :error="vehicleError" @create="createVehicle" @remove="removeVehicle" />

    <section class="rounded-2xl border border-slate-200/80 bg-white/90 p-5 shadow-sm sm:p-6">
      <div class="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div><p class="text-[11px] font-bold uppercase tracking-[.2em] text-blue-700">Browse the network</p><h2 class="mt-1 text-lg font-bold text-slate-900">Find a registered mechanic by city</h2><p class="mt-1 text-sm text-slate-500">Search registered shop profiles even when you prefer not to share device location.</p></div>
        <form class="flex w-full flex-col gap-2 sm:flex-row lg:max-w-xl" @submit.prevent="searchMechanicsByCity">
          <label for="mechanic-city-search" class="sr-only">City name</label>
          <input id="mechanic-city-search" v-model.trim="cityQuery" type="search" minlength="2" maxlength="100" placeholder="Enter a city, e.g. Lahore" class="min-h-11 min-w-0 flex-1 rounded-xl border border-slate-200 bg-slate-50 px-4 text-sm outline-none transition focus:border-blue-400 focus:bg-white focus:ring-4 focus:ring-blue-50" />
          <button type="submit" :disabled="isSearching || cityQuery.trim().length < 2" class="rounded-xl bg-slate-950 px-4 py-3 text-sm font-bold text-white transition hover:-translate-y-0.5 hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50">{{ isSearching ? 'Searching...' : 'Search city' }}</button>
          <button type="button" :disabled="isSearching" class="rounded-xl border border-slate-200 px-4 py-3 text-sm font-bold text-slate-700 transition hover:border-blue-200 hover:bg-blue-50 disabled:opacity-50" @click="browseVerifiedMechanics">Browse all</button>
          <button type="button" :disabled="isSearching || isLocating" class="rounded-xl border border-slate-200 px-4 py-3 text-sm font-bold text-slate-700 transition hover:border-blue-200 hover:bg-blue-50 disabled:opacity-50" @click="findNearbyMechanics">{{ isLocating ? 'Locating...' : 'Near me' }}</button>
        </form>
      </div>
    </section>

    <div class="grid items-start gap-8 xl:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)]">
      <div class="space-y-5">
        <AIDiagnosisForm v-model:description="description"
          :diagnosis="aiDiagnosis" :request="latestRequest"
          :loading="isSearching || isLocating" @search="findNearbyMechanics" />
        <div v-if="location" class="rounded-xl border border-slate-200 bg-white px-4 py-3 text-xs text-slate-500">
          Search location: <span class="font-mono text-slate-700">{{ formatCoordinates() }}</span>
        </div>
      </div>

        <MechanicList :location="location" :mechanics="mechanics" :loading="isSearching || isLocating" :searched="directorySearched" :city="cityQuery"
        :error="searchError" :busy-mechanic-id="busyMechanicId"
        :can-request="description.trim().length >= 10" @request-repair="requestRepair" @retry="findNearbyMechanics" />
    </div>

    <section v-if="recentRequests.length" class="space-y-4">
      <div>
        <p class="text-sm font-semibold uppercase tracking-wider text-blue-600">Your activity</p>
        <h2 class="mt-1 text-2xl font-bold tracking-tight">Recent repair requests</h2>
      </div>
      <div class="grid gap-3 md:grid-cols-2">
        <article v-for="request in recentRequests.slice(0, 4)" :key="request.id" class="group rounded-2xl border border-slate-200/80 bg-white/90 p-5 shadow-sm transition duration-300 hover:-translate-y-1 hover:shadow-xl hover:shadow-blue-950/5 [transform:perspective(1200px)_rotateX(.5deg)]">
          <div class="flex items-center justify-between gap-3">
            <p class="font-semibold text-slate-900">Request #{{ request.id.slice(0, 8) }}</p>
            <span class="rounded-full bg-amber-50 px-2.5 py-1 text-xs font-semibold capitalize text-amber-800">{{ request.status }}</span>
          </div>
          <p class="mt-2 line-clamp-2 text-sm leading-5 text-slate-600">{{ request.description }}</p>
          <p v-if="request.created_at" class="mt-2 text-[11px] text-slate-400">{{ new Date(request.created_at).toLocaleString() }}</p>
          <button v-if="request.mechanic_id && ['accepted', 'completed'].includes(request.status)" type="button" class="mt-4 rounded-lg bg-blue-50 px-3 py-2 text-xs font-bold text-blue-700 transition hover:bg-blue-100" @click="activeChatRequestId = activeChatRequestId === request.id ? '' : request.id">{{ activeChatRequestId === request.id ? 'Close chat' : 'Message mechanic' }} <span aria-hidden="true">→</span></button>
          <button v-if="request.status === 'pending'" type="button" :disabled="busyMechanicId === request.id" class="ml-2 mt-4 rounded-lg px-3 py-2 text-xs font-bold text-rose-700 transition hover:bg-rose-50 disabled:opacity-50" @click="cancelRepair(request)">{{ busyMechanicId === request.id ? 'Cancelling...' : 'Cancel request' }}</button>
        </article>
      </div>
      <div v-if="activeChatRequestId" class="mt-5 max-w-2xl"><ChatBox :request-id="activeChatRequestId" /></div>
    </section>
    <ReviewModal v-if="reviewCandidate" :request="reviewCandidate" @close="dismissReview" @submitted="onReviewSubmitted" />
  </div>
</template>
