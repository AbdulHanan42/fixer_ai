<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowLeft, Check, ImagePlus, MapPin, Sparkles, Star, Wrench } from '@lucide/vue'
import { useAuthStore } from '@/stores/auth.js'
import { useNotifications } from '@/composables/useNotifications.js'
import { repairService } from '@/services/repair.service.js'
import { vehicleService } from '@/services/vehicle.service.js'

const router = useRouter()
const auth = useAuthStore()
const { showError, showSuccess } = useNotifications()
const apiBase = new URL(import.meta.env.VITE_API_BASE_URL || 'https://fixer-ai.onrender.com/api/v1', window.location.origin)
const diagnosisUrl = new URL('/api/diagnosis/analyze', apiBase.origin)
const description = ref('')
const selectedFile = ref(null)
const previewUrl = ref('')
const vehicles = ref([])
const selectedVehicleId = ref('')
const isLoadingVehicles = ref(true)
const isAnalyzing = ref(false)
const isRequesting = ref(false)
const diagnosis = ref(null)
const recommendedMechanics = ref([])
const createdRequest = ref(null)
const errorMessage = ref('')
const requestMessage = ref('')
const allowedImageTypes = ['image/jpeg', 'image/png', 'image/webp', 'image/gif']
const canAnalyze = computed(() => description.value.trim().length >= 10 && selectedFile.value && !isAnalyzing.value)

function clearPreview() {
  if (previewUrl.value) URL.revokeObjectURL(previewUrl.value)
  previewUrl.value = ''
}

function selectImage(event) {
  const file = event.target.files?.[0] || null
  errorMessage.value = ''
  diagnosis.value = null
  recommendedMechanics.value = []
  createdRequest.value = null
  requestMessage.value = ''
  clearPreview()

  if (!file) {
    selectedFile.value = null
    return
  }
  if (!allowedImageTypes.includes(file.type)) {
    selectedFile.value = null
    event.target.value = ''
    errorMessage.value = 'Choose a JPEG, PNG, WebP, or GIF image.'
    return
  }
  if (file.size > 10 * 1024 * 1024) {
    selectedFile.value = null
    event.target.value = ''
    errorMessage.value = 'Choose an image smaller than 10 MB.'
    return
  }

  selectedFile.value = file
  previewUrl.value = URL.createObjectURL(file)
}

async function loadVehicles() {
  try {
    vehicles.value = await vehicleService.list()
  } catch {
    vehicles.value = []
  } finally {
    isLoadingVehicles.value = false
  }
}

async function analyzeIssue() {
  errorMessage.value = ''
  requestMessage.value = ''
  if (!selectedFile.value) {
    errorMessage.value = 'Choose a photo of the issue to continue.'
    return
  }
  if (description.value.trim().length < 10) {
    errorMessage.value = 'Add at least 10 characters describing the issue.'
    return
  }

  isAnalyzing.value = true
  diagnosis.value = null
  recommendedMechanics.value = []
  createdRequest.value = null
  const body = new FormData()
  body.append('image', selectedFile.value)
  body.append('description', description.value.trim())

  try {
    const response = await fetch(diagnosisUrl, {
      method: 'POST',
      headers: auth.token ? { Authorization: `Bearer ${auth.token}` } : {},
      body,
    })
    const payload = await response.json().catch(() => null)
    if (!response.ok) {
      const detail = payload?.detail
      const message = typeof detail === 'string'
        ? detail
        : Array.isArray(detail)
          ? detail.map((item) => item.msg).join(' ')
          : 'Could not analyze the image. Please try again.'
      throw new Error(message)
    }
    diagnosis.value = payload.ai_diagnosis_results
    recommendedMechanics.value = payload.recommended_mechanics || []
  } catch (error) {
    errorMessage.value = error.message || 'Could not analyze the image. Please try again.'
    showError(errorMessage.value)
  } finally {
    isAnalyzing.value = false
  }
}

async function requestRepair(mechanic) {
  if (!diagnosis.value || isRequesting.value || createdRequest.value) return
  isRequesting.value = true
  requestMessage.value = ''
  try {
    createdRequest.value = await repairService.createRepairRequest({
      description: diagnosis.value.user_description,
      mechanic_id: mechanic.id,
      vehicle_id: selectedVehicleId.value || null,
    })
    requestMessage.value = `Request sent to ${mechanic.shop_name}.`
    showSuccess(requestMessage.value)
  } catch (error) {
    requestMessage.value = error.message || 'Could not send the repair request.'
    showError(requestMessage.value)
  } finally {
    isRequesting.value = false
  }
}

function urgencyClass(urgency) {
  if (urgency === 'High') return 'border-rose-200 bg-rose-50 text-rose-800'
  if (urgency === 'Medium') return 'border-amber-200 bg-amber-50 text-amber-800'
  return 'border-emerald-200 bg-emerald-50 text-emerald-800'
}

function formatRating(value) {
  return Number(value || 0).toFixed(1)
}

onMounted(loadVehicles)
onUnmounted(clearPreview)
</script>

<template>
  <div class="space-y-8">
    <header class="flex flex-wrap items-end justify-between gap-4">
      <div>
        <p class="text-xs font-bold uppercase tracking-[.18em] text-blue-700">Customer workspace</p>
        <h1 class="mt-2 text-3xl font-bold tracking-tight text-slate-950 sm:text-4xl">AI repair assessment</h1>
        <p class="mt-2 max-w-2xl text-sm leading-6 text-slate-600">Share a photo and symptoms to find verified mechanics who offer the matching service.</p>
      </div>
      <router-link to="/customer/dashboard" class="inline-flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-3.5 py-2.5 text-sm font-semibold text-slate-700 transition hover:border-blue-200 hover:text-blue-700">
        <ArrowLeft class="size-4" aria-hidden="true" /> Back to workspace
      </router-link>
    </header>

    <div class="grid items-start gap-7 xl:grid-cols-[minmax(340px,.82fr)_minmax(0,1.18fr)]">
      <section class="rounded-xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
        <div class="flex items-center gap-3">
          <span class="grid size-10 place-items-center rounded-lg bg-blue-50 text-blue-700"><Sparkles class="size-5" aria-hidden="true" /></span>
          <div>
            <p class="text-xs font-bold uppercase tracking-wider text-blue-700">Vehicle symptoms</p>
            <h2 class="mt-0.5 text-lg font-bold text-slate-900">Describe the issue</h2>
          </div>
        </div>

        <form class="mt-6 space-y-5" @submit.prevent="analyzeIssue">
          <div>
            <label for="diagnosis-image" class="mb-2 block text-sm font-semibold text-slate-800">Photo of the issue</label>
            <label for="diagnosis-image" class="group relative flex min-h-44 cursor-pointer flex-col items-center justify-center overflow-hidden rounded-lg border border-dashed border-slate-300 bg-slate-50 text-center transition hover:border-blue-400 hover:bg-blue-50/40 focus-within:ring-4 focus-within:ring-blue-100">
              <img v-if="previewUrl" :src="previewUrl" alt="Selected vehicle issue" class="absolute inset-0 size-full object-contain" />
              <div v-else class="px-6 py-8">
                <ImagePlus class="mx-auto size-8 text-slate-400 transition group-hover:text-blue-600" aria-hidden="true" />
                <p class="mt-3 text-sm font-semibold text-slate-700">{{ selectedFile ? selectedFile.name : 'Choose an image' }}</p>
                <p class="mt-1 text-xs text-slate-500">JPEG, PNG, WebP, or GIF · up to 10 MB</p>
              </div>
              <input id="diagnosis-image" type="file" accept="image/jpeg,image/png,image/webp,image/gif" class="sr-only" @change="selectImage" />
              <span v-if="previewUrl" class="absolute inset-x-0 bottom-0 truncate bg-slate-950/75 px-3 py-2 text-left text-xs font-medium text-white">{{ selectedFile?.name }}</span>
            </label>
          </div>

          <div>
            <div class="mb-2 flex items-center justify-between gap-2">
              <label for="diagnosis-description" class="text-sm font-semibold text-slate-800">What are you noticing?</label>
              <span class="text-xs text-slate-500">{{ description.length }}/2000</span>
            </div>
            <textarea id="diagnosis-description" v-model="description" rows="5" minlength="10" maxlength="2000" required
              placeholder="For example: The engine jerks when accelerating and the red warning light is on."
              class="w-full resize-y rounded-lg border border-slate-300 px-3.5 py-3 text-sm leading-6 text-slate-900 outline-none transition placeholder:text-slate-400 focus:border-blue-500 focus:ring-4 focus:ring-blue-100"></textarea>
          </div>

          <div>
            <label for="diagnosis-vehicle" class="mb-2 block text-sm font-semibold text-slate-800">Vehicle <span class="font-normal text-slate-500">(optional)</span></label>
            <select id="diagnosis-vehicle" v-model="selectedVehicleId" :disabled="isLoadingVehicles || !vehicles.length"
              class="w-full rounded-lg border border-slate-300 bg-white px-3.5 py-3 text-sm text-slate-900 outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-100 disabled:bg-slate-100">
              <option value="">{{ isLoadingVehicles ? 'Loading your vehicles...' : vehicles.length ? 'No specific vehicle' : 'No vehicles in your garage' }}</option>
              <option v-for="vehicle in vehicles" :key="vehicle.id" :value="vehicle.id">{{ vehicle.year }} {{ vehicle.make }} {{ vehicle.model }}</option>
            </select>
          </div>

          <p v-if="errorMessage" role="alert" class="rounded-lg border border-rose-200 bg-rose-50 px-3.5 py-3 text-sm leading-5 text-rose-800">{{ errorMessage }}</p>
          <button type="submit" :disabled="!canAnalyze" class="inline-flex w-full items-center justify-center gap-2 rounded-lg bg-blue-700 px-4 py-3 text-sm font-bold text-white shadow-sm transition hover:bg-blue-800 focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-blue-200 disabled:cursor-not-allowed disabled:bg-slate-300">
            <span v-if="isAnalyzing" class="size-4 animate-spin rounded-full border-2 border-white border-r-transparent" aria-hidden="true"></span>
            <Sparkles v-else class="size-4" aria-hidden="true" />
            {{ isAnalyzing ? 'Reviewing image...' : 'Analyze and find mechanics' }}
          </button>
          <p class="text-xs leading-5 text-slate-500">This is an initial assessment, not a substitute for an in-person inspection.</p>
        </form>
      </section>

      <div class="space-y-7">
        <section v-if="diagnosis" aria-live="polite" class="border-b border-slate-200 pb-7">
          <div class="flex flex-wrap items-start justify-between gap-4">
            <div>
              <p class="text-xs font-bold uppercase tracking-[.18em] text-blue-700">AI assessment</p>
              <h2 class="mt-1 text-2xl font-bold tracking-tight text-slate-950">Possible causes</h2>
            </div>
            <span class="rounded-full border px-3 py-1.5 text-xs font-bold" :class="urgencyClass(diagnosis.urgency)">{{ diagnosis.urgency }} urgency</span>
          </div>
          <ul class="mt-5 grid gap-3 sm:grid-cols-2">
            <li v-for="(issue, index) in diagnosis.possible_issues" :key="`${index}-${issue}`" class="flex items-start gap-3 rounded-lg border border-slate-200 bg-white p-4 text-sm leading-6 text-slate-700">
              <span class="grid size-6 shrink-0 place-items-center rounded-full bg-blue-50 text-blue-700"><Check class="size-3.5" aria-hidden="true" /></span>
              {{ issue }}
            </li>
          </ul>
          <p class="mt-4 inline-flex items-center gap-2 rounded-lg bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">
            <Wrench class="size-4 text-blue-700" aria-hidden="true" /> Matching service: {{ diagnosis.target_service_category }}
          </p>
        </section>

        <section v-if="diagnosis" aria-live="polite">
          <div class="flex flex-wrap items-end justify-between gap-3">
            <div>
              <p class="text-xs font-bold uppercase tracking-[.18em] text-blue-700">Verified service providers</p>
              <h2 class="mt-1 text-2xl font-bold tracking-tight text-slate-950">Recommended mechanics</h2>
            </div>
            <span class="text-xs font-medium text-slate-500">{{ recommendedMechanics.length }} matched</span>
          </div>

          <p v-if="requestMessage" role="status" class="mt-4 rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm font-medium text-emerald-900">{{ requestMessage }}</p>
          <div v-if="!recommendedMechanics.length" class="mt-5 border-y border-slate-200 py-8 text-center">
            <p class="font-semibold text-slate-800">No verified mechanic offers this service yet.</p>
            <p class="mt-1 text-sm text-slate-500">You can keep the assessment and check again later.</p>
          </div>
          <div v-else class="mt-5 space-y-3">
            <article v-for="mechanic in recommendedMechanics" :key="mechanic.id" class="rounded-lg border border-slate-200 bg-white p-4 transition hover:border-blue-200 sm:p-5">
              <div class="flex flex-col justify-between gap-4 sm:flex-row sm:items-start">
                <div class="min-w-0">
                  <p class="text-xs font-semibold text-blue-700">{{ mechanic.name }}</p>
                  <h3 class="mt-1 truncate text-lg font-bold text-slate-950">{{ mechanic.shop_name }}</h3>
                  <p class="mt-1 text-sm leading-5 text-slate-600">{{ mechanic.address }}<span v-if="mechanic.city">, {{ mechanic.city }}</span></p>
                  <div class="mt-3 flex flex-wrap gap-x-4 gap-y-2 text-xs font-medium text-slate-600">
                    <span class="inline-flex items-center gap-1.5"><Star class="size-3.5 fill-amber-400 text-amber-500" aria-hidden="true" />{{ formatRating(mechanic.rating) }} rating</span>
                    <span class="inline-flex items-center gap-1.5"><MapPin class="size-3.5 text-slate-400" aria-hidden="true" />{{ mechanic.distance_km == null ? 'Distance unavailable' : `${Number(mechanic.distance_km).toFixed(1)} km away` }}</span>
                  </div>
                </div>
                <button type="button" :disabled="isRequesting || Boolean(createdRequest)" class="inline-flex shrink-0 items-center justify-center gap-2 rounded-lg bg-slate-950 px-4 py-2.5 text-sm font-bold text-white transition hover:bg-blue-700 focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-blue-100 disabled:cursor-not-allowed disabled:bg-slate-300" @click="requestRepair(mechanic)">
                  {{ isRequesting ? 'Sending request...' : createdRequest ? 'Request sent' : 'Send request' }}
                  <ArrowLeft class="size-4 rotate-180" aria-hidden="true" />
                </button>
              </div>
            </article>
          </div>
          <p class="mt-4 text-xs leading-5 text-slate-500">Recommendations are based on service category and verification status. Confirm the assessment with a mechanic before authorizing repairs.</p>
        </section>

        <section v-else-if="!isAnalyzing" class="flex min-h-64 flex-col items-center justify-center border-y border-dashed border-slate-300 px-6 py-10 text-center">
          <span class="grid size-12 place-items-center rounded-xl bg-blue-50 text-blue-700"><ImagePlus class="size-6" aria-hidden="true" /></span>
          <h2 class="mt-4 text-lg font-bold text-slate-900">Your assessment will appear here</h2>
          <p class="mt-1 max-w-sm text-sm leading-6 text-slate-500">Add a photo and description to see possible causes and matching verified mechanics.</p>
        </section>
        <section v-else role="status" class="grid min-h-64 place-items-center border-y border-slate-200 px-6 py-10 text-center">
          <div>
            <span class="mx-auto grid size-12 place-items-center rounded-xl bg-blue-50 text-blue-700"><span class="size-5 animate-spin rounded-full border-2 border-blue-700 border-r-transparent"></span></span>
            <h2 class="mt-4 text-lg font-bold text-slate-900">Reviewing your symptoms</h2>
            <p class="mt-1 text-sm text-slate-500">Matching the assessment to the service catalog.</p>
          </div>
        </section>
      </div>
    </div>
  </div>
</template>
