import http from '@/api/http.js'

export const authService = {
  async login(credentials) {
    return http.post('/auth/login', credentials)
  },

  async register(userData) {
    return http.post('/auth/register', userData)
  },

  async logout() {
    return http.post('/auth/logout')
  },

  async getCurrentUser() {
    return http.get('/auth/me')
  },

  async refreshToken() {
    return http.post('/auth/refresh')
  },
}
