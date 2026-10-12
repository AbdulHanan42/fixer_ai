import http from '@/api/http.js'

export const repairService = {
  createRepairRequest(request) {
    return http.post('/repairs', request)
  },

  getRepairRequest(requestId) {
    return http.get(`/repairs/${requestId}`)
  },

  getMyRepairRequests() {
    return http.get('/repairs')
  },

  getPendingRepairRequests() {
    return http.get('/repairs/pending')
  },

  updateRepairRequestStatus(requestId, status) {
    return http.put(`/repairs/${requestId}`, { status })
  },
}
