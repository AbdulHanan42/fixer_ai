import http from '@/api/http.js'

export const vehicleService = {
  list() {
    return http.get('/vehicles')
  },
  create(vehicle) {
    return http.post('/vehicles', vehicle)
  },
  update(id, vehicle) {
    return http.put(`/vehicles/${id}`, vehicle)
  },
  remove(id) {
    return http.delete(`/vehicles/${id}`)
  },
}
