import http from '@/api/http.js'

export const mechanicService = {
  getProfile() {
    return http.get('/mechanics/profile')
  },

  createProfile(profile) {
    return http.post('/mechanics/profile', profile)
  },

  updateProfile(profile) {
    return http.put('/mechanics/profile', profile)
  },

  getServices() {
    return http.get('/mechanics/services')
  },

  getServiceCatalog() {
    return http.get('/mechanics/catalog')
  },

  addService(service) {
    return http.post('/mechanics/services', service)
  },

  updateServicePrice(id, basePrice) {
    return http.put(`/mechanics/services/${id}`, { base_price: basePrice })
  },

  removeService(id) {
    return http.delete(`/mechanics/services/${id}`)
  },

  searchMechanics(params) {
    return http.get('/mechanics/search', { params })
  },

  getMechanicReviews(id) {
    return http.get(`/reviews/mechanic/${id}`)
  },
}
