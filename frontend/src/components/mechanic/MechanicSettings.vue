<script setup>
import { computed, reactive, watch } from 'vue'
import PrimaryButton from '@/components/ui/PrimaryButton.vue'
import { useLocation } from '@/composables/useLocation.js'
import { API_ORIGIN } from '@/api/http.js'

const props = defineProps({
  profile: { type: Object, default: null },
  services: { type: Array, default: () => [] },
  catalog: { type: Array, default: () => [] },
  savingProfile: { type: Boolean, default: false },
  savingService: { type: Boolean, default: false },
  savingWorkshopImage: { type: Boolean, default: false },
})

const emit = defineEmits(['save-profile', 'upload-workshop-image', 'add-service', 'add-custom-service', 'update-service', 'remove-service'])

const form = reactive({ shop_name: '', address: '', city: '', latitude: '', longitude: '' })
const selectedServiceId = defineModel('selectedServiceId', { type: String, default: '' })
const newServicePrice = defineModel('newServicePrice', { type: String, default: '' })
const customService = reactive({ name: '', category: '', base_price: '' })
const servicePrices = reactive({})
const { location, error: locationError, isLoading: isLocating, getCurrentLocation } = useLocation()

watch(() => props.profile, (profile) => {
  form.shop_name = profile?.shop_name || ''
  form.address = profile?.address || ''
  form.city = profile?.city || ''
  form.latitude = profile?.latitude ?? ''
  form.longitude = profile?.longitude ?? ''
}, { immediate: true })

watch(() => props.services, (services) => {
  for (const service of services) servicePrices[service.id] = String(service.base_price)
}, { immediate: true, deep: true })

const availableCatalog = computed(() => props.catalog.filter(
  (item) => !props.services.some((service) => service.service_id === item.id),
))

async function useCurrentLocation() {
  await getCurrentLocation()
  if (location.value) {
    form.latitude = location.value.latitude
    form.longitude = location.value.longitude
  }
}

function submitProfile() {
  emit('save-profile', {
    shop_name: form.shop_name.trim(),
    address: form.address.trim(),
    city: form.city.trim(),
    latitude: Number(form.latitude),
    longitude: Number(form.longitude),
  })
}

function addService() {
  emit('add-service', { service_id: selectedServiceId.value, base_price: Number(newServicePrice.value) })
}

function addCustomService() {
  emit('add-custom-service', { name: customService.name.trim(), category: customService.category.trim(), base_price: Number(customService.base_price) })
}

function selectWorkshopImage(event) {
  const file = event.target.files?.[0]
  if (file) emit('upload-workshop-image', file)
  event.target.value = ''
}

function workshopImageUrl(path) {
  return path ? new URL(path, API_ORIGIN).href : ''
}
</script>

<template>
  <section class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
    <div>
      <p class="text-sm font-semibold uppercase tracking-wider text-blue-600">Your shop</p>
      <h2 class="mt-1 text-xl font-bold">Profile and services</h2>
      <p class="mt-1 text-sm text-slate-600">Keep your public shop details and service prices up to date.</p>
    </div>

    <form class="mt-6 grid gap-4 sm:grid-cols-2" @submit.prevent="submitProfile">
      <div class="sm:col-span-2">
        <label for="shop-name" class="mb-1.5 block text-sm font-medium text-slate-700">Shop name</label>
        <input id="shop-name" v-model.trim="form.shop_name" required minlength="2" maxlength="100"
          class="w-full rounded-lg border border-slate-300 px-3.5 py-2.5 outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-100" />
      </div>
      <div class="sm:col-span-2">
        <label for="shop-address" class="mb-1.5 block text-sm font-medium text-slate-700">Shop address</label>
        <textarea id="shop-address" v-model.trim="form.address" rows="2" required minlength="5" maxlength="500"
          class="w-full rounded-lg border border-slate-300 px-3.5 py-2.5 outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-100"></textarea>
      </div>
      <div class="sm:col-span-2">
        <label for="shop-city" class="mb-1.5 block text-sm font-medium text-slate-700">City</label>
        <input id="shop-city" v-model.trim="form.city" required minlength="2" maxlength="100" autocomplete="address-level2" placeholder="e.g. Lahore"
          class="w-full rounded-lg border border-slate-300 px-3.5 py-2.5 outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-100" />
        <p class="mt-1 text-xs text-slate-500">Customers can find your verified shop by searching this city.</p>
      </div>
      <div>
        <label for="shop-latitude" class="mb-1.5 block text-sm font-medium text-slate-700">Latitude</label>
        <input id="shop-latitude" v-model="form.latitude" type="number" step="any" min="-90" max="90" required
          class="w-full rounded-lg border border-slate-300 px-3.5 py-2.5 outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-100" />
      </div>
      <div>
        <label for="shop-longitude" class="mb-1.5 block text-sm font-medium text-slate-700">Longitude</label>
        <input id="shop-longitude" v-model="form.longitude" type="number" step="any" min="-180" max="180" required
          class="w-full rounded-lg border border-slate-300 px-3.5 py-2.5 outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-100" />
      </div>
      <div class="flex flex-wrap items-center gap-3 sm:col-span-2">
        <PrimaryButton type="submit" :loading="savingProfile">{{ profile ? 'Save profile' : 'Create shop profile' }}</PrimaryButton>
        <button type="button" class="text-sm font-semibold text-blue-700 hover:text-blue-800" :disabled="isLocating" @click="useCurrentLocation">
          {{ isLocating ? 'Getting location...' : 'Use my current location' }}
        </button>
        <span v-if="locationError" role="alert" class="text-sm text-red-700">{{ locationError }}</span>
      </div>
    </form>

    <div class="mt-6 rounded-xl border border-slate-200 p-4">
      <div class="flex flex-wrap items-center gap-4">
        <img v-if="profile?.workshop_image_url" :src="workshopImageUrl(profile.workshop_image_url)" alt="Workshop preview"
          class="h-20 w-32 rounded-lg object-cover" />
        <div class="min-w-0 flex-1">
          <h3 class="font-bold text-slate-900">Workshop photo</h3>
          <p class="mt-1 text-sm text-slate-600">Customers see this photo behind your shop name on your profile.</p>
        </div>
        <label class="cursor-pointer rounded-lg bg-blue-700 px-4 py-2.5 text-sm font-semibold text-white hover:bg-blue-800"
          :class="{ 'pointer-events-none opacity-60': !profile || savingWorkshopImage }">
          {{ savingWorkshopImage ? 'Uploading...' : profile?.workshop_image_url ? 'Change photo' : 'Upload photo' }}
          <input type="file" accept="image/jpeg,image/png,image/webp" class="sr-only" :disabled="!profile || savingWorkshopImage"
            @change="selectWorkshopImage" />
        </label>
      </div>
      <p class="mt-2 text-xs text-slate-500">JPEG, PNG, or WebP, up to 8 MB. Create your shop profile before uploading.</p>
    </div>

    <div class="my-7 border-t border-slate-100"></div>

    <div>
      <h3 class="font-bold text-slate-900">Services and pricing</h3>
      <p class="mt-1 text-sm text-slate-600">Choose services from the platform catalog and set your base price.</p>

      <form class="mt-4 grid gap-3 sm:grid-cols-[minmax(0,1fr)_10rem_auto]" @submit.prevent="addService">
        <div>
          <label for="service-catalog" class="sr-only">Choose a service</label>
          <select id="service-catalog" v-model="selectedServiceId" required :disabled="!profile || !availableCatalog.length"
            class="w-full rounded-lg border border-slate-300 bg-white px-3.5 py-2.5 outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-100 disabled:bg-slate-100">
            <option value="" disabled>{{ availableCatalog.length ? 'Choose a service' : 'No more services available' }}</option>
            <option v-for="item in availableCatalog" :key="item.id" :value="item.id">{{ item.name }} · {{ item.category }}</option>
          </select>
        </div>
        <div>
          <label for="service-price" class="sr-only">Base price</label>
          <input id="service-price" v-model="newServicePrice" type="number" min="0.01" step="0.01" required placeholder="Base price"
            :disabled="!profile"
            class="w-full rounded-lg border border-slate-300 px-3.5 py-2.5 outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-100 disabled:bg-slate-100" />
        </div>
        <PrimaryButton type="submit" :loading="savingService" :disabled="!profile || !availableCatalog.length">Add service</PrimaryButton>
      </form>

      <form class="mt-3 grid gap-3 rounded-xl border border-blue-100 bg-blue-50/50 p-3 sm:grid-cols-[minmax(0,1fr)_minmax(0,1fr)_9rem_auto]" @submit.prevent="addCustomService">
        <input v-model.trim="customService.name" aria-label="Custom service name" required minlength="2" maxlength="100" placeholder="Write a custom service" :disabled="!profile || savingService" class="w-full rounded-lg border border-slate-300 bg-white px-3.5 py-2.5 outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-100 disabled:bg-slate-100" />
        <input v-model.trim="customService.category" aria-label="Service category" required minlength="2" maxlength="50" placeholder="Category" :disabled="!profile || savingService" class="w-full rounded-lg border border-slate-300 bg-white px-3.5 py-2.5 outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-100 disabled:bg-slate-100" />
        <input v-model="customService.base_price" aria-label="Base price" type="number" min="0.01" step="0.01" required placeholder="Base price" :disabled="!profile || savingService" class="w-full rounded-lg border border-slate-300 bg-white px-3.5 py-2.5 outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-100 disabled:bg-slate-100" />
        <PrimaryButton type="submit" :loading="savingService" :disabled="!profile">Add custom</PrimaryButton>
      </form>

      <p v-if="!profile" class="mt-2 text-xs text-slate-500">Create your shop profile before adding services.</p>
      <p v-else-if="!catalog.length" class="mt-2 text-xs text-slate-500">The service catalog is empty. Ask an administrator to add services.</p>

      <ul v-if="services.length" class="mt-5 divide-y divide-slate-100 rounded-xl border border-slate-200">
        <li v-for="service in services" :key="service.id" class="flex flex-wrap items-center gap-3 p-3 sm:p-4">
          <div class="min-w-0 flex-1">
            <p class="truncate font-semibold text-slate-900">{{ service.service_name || 'Service' }}</p>
            <p class="text-xs text-slate-500">{{ service.service_category || 'General' }}</p>
          </div>
          <label :for="`price-${service.id}`" class="sr-only">Base price for {{ service.service_name }}</label>
          <input :id="`price-${service.id}`" v-model="servicePrices[service.id]" type="number" min="0.01" step="0.01"
            class="w-28 rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-100" />
          <button type="button" class="text-sm font-semibold text-blue-700 hover:text-blue-800"
            :disabled="savingService" @click="$emit('update-service', service.id, Number(servicePrices[service.id]))">Save</button>
          <button type="button" class="text-sm font-semibold text-red-700 hover:text-red-800"
            :disabled="savingService" @click="$emit('remove-service', service.id)">Remove</button>
        </li>
      </ul>
      <div v-else-if="profile" class="mt-4 rounded-xl border border-dashed border-slate-300 bg-slate-50 p-5 text-center text-sm text-slate-500">
        You haven’t added any services yet.
      </div>
    </div>
  </section>
</template>
