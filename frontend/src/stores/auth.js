import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import http from '@/api/http.js'

const TOKEN_KEY = 'fix-ai-token'
const USER_KEY = 'fix-ai-user'

function readUser() {
  try {
    return JSON.parse(localStorage.getItem(USER_KEY) || 'null')
  } catch {
    localStorage.removeItem(USER_KEY)
    return null
  }
}

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem(TOKEN_KEY))
  const user = ref(readUser())
  const isAuthenticated = computed(() => Boolean(token.value))
  const isCustomer = computed(() => user.value?.role === 'customer')
  const isMechanic = computed(() => user.value?.role === 'mechanic')
  const isAdmin = computed(() => user.value?.role === 'admin')

  function setToken(value) {
    token.value = value || null
    if (token.value) localStorage.setItem(TOKEN_KEY, token.value)
    else localStorage.removeItem(TOKEN_KEY)
  }

  function setUser(value) {
    user.value = value || null
    if (user.value) localStorage.setItem(USER_KEY, JSON.stringify(user.value))
    else localStorage.removeItem(USER_KEY)
  }

  async function login(email, password) {
    const form = new URLSearchParams({ email, password })
    const result = await http.post('/auth/login', form)
    setToken(result.access_token)

    try {
      setUser(await http.get('/auth/me'))
      return user.value
    } catch (error) {
      setToken(null)
      setUser(null)
      throw error
    }
  }

  async function logout() {
    setToken(null)
    setUser(null)
    const { default: router } = await import('@/router/index.js')
    if (router.currentRoute.value.path !== '/login') await router.replace('/login')
  }

  return {
    token,
    user,
    isAuthenticated,
    isCustomer,
    isMechanic,
    isAdmin,
    setToken,
    setUser,
    login,
    logout,
  }
})
