import { useAuthStore } from '@/stores/auth.js'

export function useAuth() {
  const authStore = useAuthStore()

  return {
    user: authStore.user,
    token: authStore.token,
    isAuthenticated: authStore.isAuthenticated,
    login: (credentials) => {
      authStore.setUser(credentials.user)
      authStore.setToken(credentials.token)
    },
    logout: () => {
      authStore.logout()
    },
  }
}
