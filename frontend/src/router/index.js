import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth.js'
import http from '@/api/http.js'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      component: () => import('@/layouts/PublicLayout.vue'),
      children: [
        { path: '', name: 'home', component: () => import('@/views/public/LandingPage.vue') },
      ],
    },
    {
      path: '/login',
      component: () => import('@/layouts/AuthLayout.vue'),
      children: [
        { path: '', name: 'login', component: () => import('@/views/auth/Login.vue') },
      ],
    },
    {
      path: '/register',
      component: () => import('@/layouts/AuthLayout.vue'),
      children: [
        { path: '', name: 'register', component: () => import('@/views/auth/Register.vue') },
      ],
    },
    {
      path: '/customer/dashboard',
      component: () => import('@/layouts/AppLayout.vue'),
      meta: { requiresAuth: true, role: 'customer' },
      children: [
        { path: '', name: 'customer-dashboard', component: () => import('@/views/customer/Dashboard.vue') },
      ],
    },
    {
      path: '/customer/diagnosis',
      component: () => import('@/layouts/AppLayout.vue'),
      meta: { requiresAuth: true, role: 'customer' },
      children: [
        { path: '', name: 'customer-ai-diagnosis', component: () => import('@/views/customer/AIDiagnosis.vue') },
      ],
    },
    {
      path: '/mechanic/dashboard',
      component: () => import('@/layouts/AppLayout.vue'),
      meta: { requiresAuth: true, role: 'mechanic' },
      children: [
        { path: '', name: 'mechanic-dashboard', component: () => import('@/views/mechanic/Dashboard.vue') },
      ],
    },
    {
      path: '/admin/dashboard',
      component: () => import('@/layouts/AppLayout.vue'),
      meta: { requiresAuth: true, role: 'admin' },
      children: [
        { path: '', name: 'admin-dashboard', component: () => import('@/views/admin/AdminDashboard.vue') },
      ],
    },
    { path: '/:pathMatch(.*)*', name: 'not-found', component: () => import('@/views/errors/NotFoundPage.vue') },
  ],
})

function dashboardForRole(role) {
  if (role === 'mechanic') return '/mechanic/dashboard'
  if (role === 'admin') return '/admin/dashboard'
  if (role === 'customer') return '/customer/dashboard'
  return '/login'
}

router.beforeEach(async (to) => {
  const auth = useAuthStore()

  if (to.name === 'login' || to.name === 'register') {
    if (auth.isAuthenticated && auth.user) return dashboardForRole(auth.user.role)
    return true
  }
  if (!to.meta.requiresAuth) return true
  if (!auth.isAuthenticated) return { name: 'login', query: { redirect: to.fullPath } }

  if (!auth.user) {
    try {
      auth.setUser(await http.get('/auth/me'))
    } catch {
      auth.setToken(null)
      auth.setUser(null)
      return { name: 'login', query: { redirect: to.fullPath } }
    }
  }

  if (auth.user?.role !== to.meta.role) return dashboardForRole(auth.user?.role)
  return true
})

export default router
