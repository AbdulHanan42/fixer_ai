import api from './api.js'

export const mechanicService = {
  async searchMechanics(params) {
    return api.get('/mechanics', { params })
  },

  async getMechanicById(id) {
    return api.get(`/mechanics/${id}`)
  },

  async getMechanicReviews(id) {
    return api.get(`/mechanics/${id}/reviews`)
  },

  async submitReview(id, reviewData) {
    return api.post(`/mechanics/${id}/reviews`, reviewData)
  },

  async sendRepairRequest(mechanicId, requestData) {
    return api.post(`/mechanics/${mechanicId}/requests`, requestData)
  },
}
