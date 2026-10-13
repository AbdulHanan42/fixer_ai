<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import JobQueue from '@/components/mechanic/JobQueue.vue'
import MechanicSettings from '@/components/mechanic/MechanicSettings.vue'
import ChatBox from '@/components/chat/ChatBox.vue'
import PrimaryButton from '@/components/ui/PrimaryButton.vue'
import StatusBadge from '@/components/ui/StatusBadge.vue'
import { useNotifications } from '@/composables/useNotifications.js'
import { mechanicService } from '@/services/mechanic.service.js'
import { repairService } from '@/services/repair.service.js'

const { showError, showSuccess } = useNotifications()
const route = useRoute()

const profile = ref(null)
const mechanicServices = ref([])
const serviceCatalog = ref([])
const pendingRequests = ref([])
const assignedRequests = ref([])
const selectedServiceId = ref('')
const newServicePrice = ref('')
const pageError = ref('')
const queueError = ref('')
const isLoading = ref(true)
const isRefreshing = ref(false)
const isQueueLoading = ref(true)
const isSavingProfile = ref(false)
const isSavingService = ref(false)
const isSavingWorkshopImage = ref(false)
const isSavingAvailability = ref(false)
const busyRequestId = ref('')
const activeChatRequestId = ref('')

watch(() => route.query.chat, (requestId) => {
  activeChatRequestId.value = typeof requestId === 'string' ? requestId : ''
}, { immediate: true })

const actionableRequests = computed(() => {
  if (!profile.value) return []
  return pendingRequests.value.filter(
    (request) => !request.mechanic_id || request.mechanic_id === profile.value.id,
  )
})

const activeJobs = computed(() => assignedRequests.value.filter((request) => request.status === 'accepted'))
const isOnline = computed(() => Boolean(profile.value?.is_online))

async function loadDashboard({ silent = false } = {}) {
  if (silent) isRefreshing.value = true
  else isLoading.value = true
  pageError.value = ''
  queueError.value = ''

  try {
    try {
      profile.value = await mechanicService.getProfile()
    } catch (error) {
      if (error.status === 404) profile.value = null
      else throw error
    }

    const [pendingResult, catalogResult] = await Promise.allSettled([
      repairService.getPendingRepairRequests(),
      mechanicService.getServiceCatalog(),
    ])
    if (pendingResult.status === 'fulfilled') pendingRequests.value = pendingResult.value
    else queueError.value = pendingResult.reason.message || 'Could not load the request queue.'
    isQueueLoading.value = false
    if (catalogResult.status === 'fulfilled') serviceCatalog.value = catalogResult.value

    if (profile.value) {
      const [servicesResult, requestsResult] = await Promise.allSettled([
        mechanicService.getServices(),
        repairService.getMyRepairRequests(),
      ])
      if (servicesResult.status === 'fulfilled') mechanicServices.value = servicesResult.value
      else pageError.value = servicesResult.reason.message || 'Could not load your service list.'
      if (requestsResult.status === 'fulfilled') assignedRequests.value = requestsResult.value
      else pageError.value ||= requestsResult.reason.message || 'Could not load your assigned jobs.'
    } else {
      mechanicServices.value = []
      assignedRequests.value = []
    }
  } catch (error) {
    pageError.value = error.message || 'Could not load the mechanic dashboard.'
  } finally {
    isLoading.value = false
    isRefreshing.value = false
    isQueueLoading.value = false
  }
}

async function refreshQueue() {
  isQueueLoading.value = true
  queueError.value = ''
  try {
    pendingRequests.value = await repairService.getPendingRepairRequests()
  } catch (error) {
    queueError.value = error.message || 'Could not refresh the request queue.'
  } finally {
    isQueueLoading.value = false
  }
}

async function toggleAvailability() {
  if (!profile.value) {
    showError('Create your shop profile before changing availability.')
    return
  }

  isSavingAvailability.value = true
  const nextValue = !isOnline.value
  try {
    profile.value = await mechanicService.updateProfile({ is_online: nextValue })
    showSuccess(nextValue ? 'You are now online and visible to nearby customers.' : 'You are now offline.')
  } catch (error) {
    showError(error.message || 'Could not update your availability.')
  } finally {
    isSavingAvailability.value = false
  }
}

async function saveProfile(profileData) {
  isSavingProfile.value = true
  try {
    profile.value = profile.value
      ? await mechanicService.updateProfile(profileData)
      : await mechanicService.createProfile(profileData)
    showSuccess('Shop profile saved.')
    await loadDashboard({ silent: true })
  } catch (error) {
    showError(error.message || 'Could not save your shop profile.')
  } finally {
    isSavingProfile.value = false
  }
}

async function uploadWorkshopImage(file) {
  isSavingWorkshopImage.value = true
  try {
    profile.value = await mechanicService.uploadWorkshopImage(file)
    showSuccess('Workshop photo updated.')
  } catch (error) {
    showError(error.message || 'Could not upload the workshop photo.')
  } finally {
    isSavingWorkshopImage.value = false
  }
}

async function updateRequestStatus(request, status) {
  busyRequestId.value = request.id
  queueError.value = ''
  try {
    const updated = await repairService.updateRepairRequestStatus(request.id, status)
    pendingRequests.value = pendingRequests.value.filter((item) => item.id !== request.id)
    if (status === 'accepted') {
      assignedRequests.value = [updated, ...assignedRequests.value.filter((item) => item.id !== request.id)]
      showSuccess('Repair request accepted and assigned to your shop.')
    } else {
      showSuccess('Repair request rejected.')
    }
  } catch (error) {
    queueError.value = error.message || 'Could not update this repair request.'
  } finally {
    busyRequestId.value = ''
  }
}

async function markJobCompleted(request) {
  busyRequestId.value = request.id
  try {
    const updated = await repairService.updateRepairRequestStatus(request.id, 'completed')
    assignedRequests.value = assignedRequests.value.map((item) => item.id === updated.id ? updated : item)
    showSuccess('Job marked as completed.')
  } catch (error) {
    showError(error.message || 'Could not complete this job.')
  } finally {
    busyRequestId.value = ''
  }
}

async function addService(service) {
  isSavingService.value = true
  try {
    const created = await mechanicService.addService(service)
    mechanicServices.value = [...mechanicServices.value, created]
    selectedServiceId.value = ''
    newServicePrice.value = ''
    showSuccess('Service added to your profile.')
  } catch (error) {
    showError(error.message || 'Could not add this service.')
  } finally {
    isSavingService.value = false
  }
}

async function updateServicePrice(id, price) {
  if (!Number.isFinite(price) || price <= 0) {
    showError('Enter a price greater than zero.')
    return
  }
  isSavingService.value = true
  try {
    const updated = await mechanicService.updateServicePrice(id, price)
    mechanicServices.value = mechanicServices.value.map((service) => service.id === id ? updated : service)
    showSuccess('Service price updated.')
  } catch (error) {
    showError(error.message || 'Could not update this service price.')
  } finally {
    isSavingService.value = false
  }
}

async function removeService(id) {
  isSavingService.value = true
  try {
    await mechanicService.removeService(id)
    mechanicServices.value = mechanicServices.value.filter((service) => service.id !== id)
    showSuccess('Service removed from your profile.')
  } catch (error) {
    showError(error.message || 'Could not remove this service.')
  } finally {
    isSavingService.value = false
  }
}

let queueRefreshTimer
onMounted(() => {
  loadDashboard()
  queueRefreshTimer = window.setInterval(refreshQueue, 30000)
})
onUnmounted(() => window.clearInterval(queueRefreshTimer))
</script>

<template>
  <div class="space-y-8">
    <section class="flex flex-col justify-between gap-5 lg:flex-row lg:items-end">
      <div>
        <p class="text-sm font-semibold uppercase tracking-wider text-blue-600">Mechanic workspace</p>
        <h1 class="mt-2 text-3xl font-bold tracking-tight sm:text-4xl">Your work, in one place</h1>
        <p class="mt-3 text-slate-600">Manage your availability, respond to repair requests, and keep your shop details current.</p>
      </div>
      <div class="flex flex-wrap items-center gap-3">
        <StatusBadge :status="isOnline ? 'online' : 'offline'" :label="isOnline ? 'Online' : 'Offline'" />
        <button type="button" role="switch" :aria-checked="isOnline" :aria-label="isOnline ? 'Set availability offline' : 'Set availability online'"
          :disabled="!profile || isSavingAvailability" @click="toggleAvailability"
          :class="isOnline ? 'bg-emerald-600' : 'bg-slate-300'"
          class="relative inline-flex h-8 w-14 items-center rounded-full transition-colors focus:outline-none focus:ring-4 focus:ring-blue-100 disabled:cursor-not-allowed disabled:opacity-50">
          <span :class="isOnline ? 'translate-x-7' : 'translate-x-1'" class="inline-block size-6 transform rounded-full bg-white shadow transition-transform"></span>
        </button>
        <button type="button" class="rounded-lg p-2 text-sm font-semibold text-slate-600 hover:bg-slate-100"
          :disabled="isRefreshing" @click="loadDashboard({ silent: true })">Refresh data</button>
      </div>
    </section>

    <p v-if="pageError" role="alert" class="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">{{ pageError }}</p>
    <div v-if="isLoading" class="grid min-h-56 place-items-center rounded-2xl border border-slate-200 bg-white text-slate-600" role="status">
      Loading your mechanic workspace...
    </div>
    <template v-else>
      <div v-if="!profile" class="rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm leading-6 text-amber-900">
        Set up your shop profile to go online, appear in customer searches, and manage repair requests.
      </div>

      <JobQueue :requests="actionableRequests" :loading="isQueueLoading" :busy-request-id="busyRequestId"
        :error="queueError" :actions-disabled="!isOnline" @refresh="refreshQueue"
        @update-status="updateRequestStatus" />

      <section v-if="activeJobs.length" class="space-y-4">
        <div>
          <p class="text-sm font-semibold uppercase tracking-wider text-blue-600">In progress</p>
          <h2 class="mt-1 text-2xl font-bold tracking-tight">Accepted jobs</h2>
        </div>
        <div class="grid gap-4 lg:grid-cols-2">
          <article v-for="job in activeJobs" :key="job.id" class="rounded-2xl border border-slate-200/80 bg-white/90 p-5 shadow-sm transition duration-300 hover:-translate-y-1 hover:shadow-xl hover:shadow-blue-950/5 [transform:perspective(1200px)_rotateX(.5deg)]">
            <div class="flex items-center justify-between gap-3">
              <h3 class="font-bold text-slate-900">Request #{{ job.id.slice(0, 8) }}</h3>
              <StatusBadge :status="job.status" />
            </div>
            <p class="mt-3 whitespace-pre-line text-sm leading-6 text-slate-700">{{ job.description }}</p>
            <div class="mt-5 flex flex-wrap gap-2">
              <PrimaryButton :loading="busyRequestId === job.id" :disabled="Boolean(busyRequestId)" @click="markJobCompleted(job)">Mark completed</PrimaryButton>
              <button type="button" class="rounded-xl border border-blue-200 px-4 py-2 text-sm font-bold text-blue-700 transition hover:bg-blue-50" @click="activeChatRequestId = activeChatRequestId === job.id ? '' : job.id">{{ activeChatRequestId === job.id ? 'Close chat' : 'Open chat' }}</button>
            </div>
          </article>
        </div>
      </section>
      <section v-if="activeChatRequestId" class="max-w-2xl">
        <ChatBox :request-id="activeChatRequestId" />
      </section>

      <MechanicSettings :profile="profile" :services="mechanicServices" :catalog="serviceCatalog"
        :saving-profile="isSavingProfile" :saving-service="isSavingService"
        :saving-workshop-image="isSavingWorkshopImage"
        v-model:selected-service-id="selectedServiceId" v-model:new-service-price="newServicePrice"
        @save-profile="saveProfile" @upload-workshop-image="uploadWorkshopImage" @add-service="addService"
        @update-service="updateServicePrice" @remove-service="removeService" />
    </template>
  </div>
</template>
