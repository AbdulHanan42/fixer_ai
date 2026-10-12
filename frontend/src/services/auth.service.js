import http from '@/api/http.js'

export const authService = {
  async login(credentials) {
    return http.post('/auth/login', credentials)
  },

  async register(userData) {
    return http.post('/auth/register', userData)
  },

  async getCurrentUser() {
    return http.get('/auth/me')
  },
}
