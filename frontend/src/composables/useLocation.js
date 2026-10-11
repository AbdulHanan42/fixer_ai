import { ref } from 'vue'
import { locationService } from '@/services/location.service.js'

export function useLocation() {
  const location = ref(null)
  const error = ref(null)
  const isLoading = ref(false)

  async function getCurrentLocation() {
    isLoading.value = true
    error.value = null
    try {
      location.value = await locationService.getCurrentPosition()
    } catch (err) {
      error.value = err.message
    } finally {
      isLoading.value = false
    }
  }

  function calculateDistance(lat1, lon1, lat2, lon2) {
    return locationService.calculateDistance(lat1, lon1, lat2, lon2)
  }

  return {
    location,
    error,
    isLoading,
    getCurrentLocation,
    calculateDistance,
  }
}
