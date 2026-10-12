<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth.js'
import PrimaryButton from '@/components/ui/PrimaryButton.vue'
import { useNotifications } from '@/composables/useNotifications.js'

const email = ref('')
const password = ref('')
const errorMessage = ref('')
const isSubmitting = ref(false)
const auth = useAuthStore()
const { showSuccess } = useNotifications()
const route = useRoute()
const router = useRouter()

function dashboardForRole(role) {
  if (role === 'mechanic') return '/mechanic/dashboard'
  if (role === 'admin') return '/admin/dashboard'
  return '/customer/dashboard'
}

async function submitLogin() {
  errorMessage.value = ''
  isSubmitting.value = true
  try {
    const user = await auth.login(email.value, password.value)
    showSuccess(`Welcome back, ${user.full_name}.`)
    const roleDashboard = dashboardForRole(user.role)
    const requestedPath = typeof route.query.redirect === 'string' ? route.query.redirect : null
    const allowedRedirect = requestedPath && requestedPath.startsWith(roleDashboard) ? requestedPath : roleDashboard
    await router.replace(allowedRedirect)
  } catch (error) {
    errorMessage.value = error.message || 'Unable to sign in. Please try again.'
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <section class="mx-auto max-w-md px-4 py-12 sm:py-16">
    <div class="rounded-2xl border border-slate-200 bg-white p-7 shadow-sm sm:p-9">
      <p class="text-sm font-semibold uppercase tracking-wider text-blue-600">Welcome back</p>
      <h1 class="mt-2 text-3xl font-bold tracking-tight text-slate-900">Sign in to Fixer AI</h1>
      <p class="mt-2 text-sm leading-6 text-slate-600">Access your dashboard and keep your car moving.</p>

      <form class="mt-8 space-y-5" @submit.prevent="submitLogin">
        <div>
          <label for="email" class="mb-2 block text-sm font-medium text-slate-700">Email address</label>
          <input id="email" v-model="email" type="email" autocomplete="email" required
            class="w-full rounded-lg border border-slate-300 px-3.5 py-3 text-slate-900 outline-none transition placeholder:text-slate-400 focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
            placeholder="you@example.com" />
        </div>
        <div>
          <label for="password" class="mb-2 block text-sm font-medium text-slate-700">Password</label>
          <input id="password" v-model="password" type="password" autocomplete="current-password" required
            class="w-full rounded-lg border border-slate-300 px-3.5 py-3 text-slate-900 outline-none transition placeholder:text-slate-400 focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
            placeholder="Enter your password" />
        </div>
        <p v-if="errorMessage" role="alert" class="rounded-lg bg-red-50 px-3.5 py-3 text-sm text-red-700">{{ errorMessage }}</p>
        <PrimaryButton type="submit" :loading="isSubmitting" class="w-full">
          {{ isSubmitting ? 'Signing in...' : 'Sign in' }}
        </PrimaryButton>
      </form>
      <p class="mt-6 text-center text-sm text-slate-600">
        New to Fixer AI? <router-link to="/register" class="font-semibold text-blue-700 hover:text-blue-800">Create an account</router-link>
      </p>
    </div>
  </section>
</template>
