import { ref } from 'vue'
import { defineStore } from 'pinia'

export const useMechanicStore = defineStore('mechanic', () => {
  const mechanics = ref([])
  const selectedMechanic = ref(null)
  const searchQuery = ref('')
  const filters = ref({
    distance: null,
    rating: null,
    services: [],
    verified: false,
  })

  function setMechanics(mechanicList) {
    mechanics.value = mechanicList
  }

  function setSelectedMechanic(mechanic) {
    selectedMechanic.value = mechanic
  }

  function setSearchQuery(query) {
    searchQuery.value = query
  }

  function setFilters(newFilters) {
    filters.value = { ...filters.value, ...newFilters }
  }

  return {
    mechanics,
    selectedMechanic,
    searchQuery,
    filters,
    setMechanics,
    setSelectedMechanic,
    setSearchQuery,
    setFilters,
  }
})
