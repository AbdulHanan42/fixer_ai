import api from './api.js'

export const authService = {
  async login(credentials) {
    return api.post('/auth/login', credentials)
  },

  async register(userData) {
    return api.post('/auth/register', userData)
  },

  async logout() {
    return api.post('/auth/logout')
  },

  async getCurrentUser() {
    return api.get('/auth/me')
  },

  async refreshToken() {
    return api.post('/auth/refresh')
  },
}
