<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Eye, EyeOff } from '@lucide/vue'
import { useAuthStore } from '@/stores/auth.js'
import PrimaryButton from '@/components/ui/PrimaryButton.vue'
import { useNotifications } from '@/composables/useNotifications.js'
import loginBackground from '@/assets/images/backui.jpg'

const email = ref('')
const password = ref('')
const showPassword = ref(false)
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
  <section
    class="relative isolate flex min-h-[calc(100svh-4rem)] items-center overflow-hidden bg-cover bg-center px-4 py-10 sm:px-6 lg:px-8"
    :style="{ backgroundImage: `linear-gradient(90deg, rgba(7, 17, 31, .72), rgba(7, 17, 31, .42)), url(${loginBackground})` }"
  >
    <div class="relative mx-auto grid w-full max-w-7xl items-center gap-10 lg:grid-cols-[minmax(0,1fr)_minmax(400px,460px)] lg:gap-16">
      <div class="hidden max-w-xl text-white lg:block">
        <p class="text-sm font-bold uppercase tracking-[0.18em] text-blue-200">Help for the road ahead</p>
        <h1 class="mt-5 text-5xl font-bold leading-[1.08] tracking-tight">When the road gets difficult, you’re not on your own.</h1>
        <p class="mt-5 max-w-lg text-lg leading-8 text-white/80">Find trusted automotive help, stay in touch, and keep every repair moving forward.</p>
        <div class="mt-9 flex flex-wrap gap-x-6 gap-y-2 text-sm font-medium text-white/90">
          <span>Local mechanics</span>
          <span>Clear repair updates</span>
          <span>Help when you need it</span>
        </div>
      </div>

      <div class="mx-auto w-full max-w-md rounded-2xl border border-white/70 bg-white p-7 shadow-2xl shadow-slate-950/20 sm:p-9">
        <p class="text-sm font-semibold uppercase tracking-wider text-blue-600">Welcome back</p>
        <h2 class="mt-2 text-3xl font-bold tracking-tight text-slate-900">Sign in to Fixer AI</h2>
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
            <div class="relative">
              <input id="password" v-model="password" :type="showPassword ? 'text' : 'password'" autocomplete="current-password" required
                class="w-full rounded-lg border border-slate-300 px-3.5 py-3 pr-12 text-slate-900 outline-none transition placeholder:text-slate-400 focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
                placeholder="Enter your password" />
              <button type="button" :aria-label="showPassword ? 'Hide password' : 'Show password'" :aria-pressed="showPassword"
                class="absolute inset-y-0 right-0 grid w-11 place-items-center text-slate-500 transition hover:text-slate-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-blue-500"
                @click="showPassword = !showPassword">
                <EyeOff v-if="showPassword" class="size-5" aria-hidden="true" />
                <Eye v-else class="size-5" aria-hidden="true" />
              </button>
            </div>
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
    </div>
  </section>
</template>
