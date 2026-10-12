import { useAuthStore } from '@/stores/auth.js'

export function useAuth() {
  const authStore = useAuthStore()

  return {
    user: authStore.user,
    token: authStore.token,
    isAuthenticated: authStore.isAuthenticated,
    login: (credentials) => authStore.login(credentials.email, credentials.password),
    logout: () => authStore.logout(),
  }
}
