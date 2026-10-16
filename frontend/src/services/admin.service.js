import http from '@/api/http.js'

export const adminService = {
  getPendingMechanics() {
    return http.get('/admin/mechanics/pending')
  },
  verifyMechanic(mechanicId) {
    return http.patch(`/admin/mechanics/${mechanicId}/verify`)
  },
}
