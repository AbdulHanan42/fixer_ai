<script setup>
import { computed, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Check, Eye, EyeOff } from '@lucide/vue'
import PrimaryButton from '@/components/ui/PrimaryButton.vue'
import { useNotifications } from '@/composables/useNotifications.js'
import { authService } from '@/services/auth.service.js'
import registerBackground from '@/assets/images/backui1.jpg'

const router = useRouter()
const { showSuccess } = useNotifications()
const form = reactive({ full_name: '', email: '', phone_number: '', password: '', role: 'customer' })
const showPassword = ref(false)
const errorMessage = ref('')
const isSubmitting = ref(false)
const passwordRules = computed(() => [
  { label: 'At least 8 characters', valid: form.password.length >= 8 },
  { label: 'One uppercase letter', valid: /[A-Z]/.test(form.password) },
  { label: 'One number', valid: /[0-9]/.test(form.password) },
  { label: 'One special character', valid: /[^A-Za-z0-9]/.test(form.password) },
])
const passwordScore = computed(() => passwordRules.value.filter((rule) => rule.valid).length)
const passwordStrength = computed(() => {
  if (passwordScore.value === 4) return 'Strong'
  if (passwordScore.value >= 2) return 'Fair'
  return form.password ? 'Weak' : 'Not set'
})

async function submitRegistration() {
  errorMessage.value = ''
  if (passwordScore.value !== passwordRules.value.length) {
    errorMessage.value = 'Use at least 8 characters with an uppercase letter, a number, and a special character.'
    return
  }
  isSubmitting.value = true
  try {
    await authService.register(form)
    showSuccess('Your account is ready. Sign in to continue.')
    await router.replace('/login')
  } catch (error) {
    errorMessage.value = error.message || 'Unable to create your account. Please try again.'
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <section
    class="relative isolate flex min-h-[calc(100svh-4rem)] items-center overflow-hidden bg-cover bg-center px-4 py-8 sm:px-6 lg:px-8"
    :style="{ backgroundImage: `linear-gradient(90deg, rgba(7, 17, 31, .72), rgba(7, 17, 31, .42)), url(${registerBackground})` }"
  >
    <div class="relative mx-auto grid w-full max-w-7xl items-center gap-8 lg:grid-cols-[minmax(0,1fr)_minmax(480px,540px)] lg:gap-14">
      <div class="hidden max-w-xl text-white lg:block">
        <p class="text-sm font-bold uppercase tracking-[0.18em] text-blue-200">Get back on the road</p>
        <h1 class="mt-5 text-5xl font-bold leading-[1.08] tracking-tight">A little help can change the whole journey.</h1>
        <p class="mt-5 max-w-lg text-lg leading-8 text-white/80">Create your account to connect with automotive professionals and manage your repair in one place.</p>
        <div class="mt-9 flex flex-wrap gap-x-6 gap-y-2 text-sm font-medium text-white/90">
          <span>Find local help</span>
          <span>Stay in the loop</span>
          <span>Move forward with confidence</span>
        </div>
      </div>

      <div class="mx-auto w-full max-w-lg rounded-2xl border border-white/70 bg-white p-6 shadow-2xl shadow-slate-950/20 sm:p-8">
        <p class="text-sm font-semibold uppercase tracking-wider text-blue-600">Get started</p>
        <h2 class="mt-2 text-3xl font-bold tracking-tight text-slate-900">Create your account</h2>
        <p class="mt-2 text-sm leading-6 text-slate-600">Join Fixer AI to connect with trusted automotive help.</p>

        <form class="mt-7 grid gap-5 sm:grid-cols-2" @submit.prevent="submitRegistration">
          <div class="sm:col-span-2">
            <label for="full-name" class="mb-2 block text-sm font-medium text-slate-700">Full name</label>
            <input id="full-name" v-model.trim="form.full_name" type="text" autocomplete="name" minlength="2" maxlength="100" required
              class="w-full rounded-lg border border-slate-300 px-3.5 py-3 outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-100" />
          </div>
          <div>
            <label for="register-email" class="mb-2 block text-sm font-medium text-slate-700">Email address</label>
            <input id="register-email" v-model.trim="form.email" type="email" autocomplete="email" required
              class="w-full rounded-lg border border-slate-300 px-3.5 py-3 outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-100" />
          </div>
          <div>
            <label for="phone-number" class="mb-2 block text-sm font-medium text-slate-700">Phone number</label>
            <input id="phone-number" v-model.trim="form.phone_number" type="tel" autocomplete="tel" minlength="10" maxlength="15" required
              placeholder="+1 555 123 4567"
              class="w-full rounded-lg border border-slate-300 px-3.5 py-3 outline-none placeholder:text-slate-400 focus:border-blue-500 focus:ring-4 focus:ring-blue-100" />
          </div>
          <div class="sm:col-span-2">
            <label for="register-password" class="mb-2 block text-sm font-medium text-slate-700">Password</label>
            <div class="relative">
              <input id="register-password" v-model="form.password" :type="showPassword ? 'text' : 'password'" autocomplete="new-password" minlength="8" maxlength="100" pattern="(?=.*[A-Z])(?=.*[0-9])(?=.*[^A-Za-z0-9]).{8,100}" title="Use at least 8 characters with an uppercase letter, a number, and a special character." required
                class="w-full rounded-lg border border-slate-300 px-3.5 py-3 pr-12 outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-100" />
              <button type="button" :aria-label="showPassword ? 'Hide password' : 'Show password'" :aria-pressed="showPassword"
                class="absolute inset-y-0 right-0 grid w-11 place-items-center text-slate-500 transition hover:text-slate-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-blue-500"
                @click="showPassword = !showPassword">
                <EyeOff v-if="showPassword" class="size-5" aria-hidden="true" />
                <Eye v-else class="size-5" aria-hidden="true" />
              </button>
            </div>
          </div>
          <div class="sm:col-span-2" aria-live="polite">
            <div class="flex items-center justify-between text-xs">
              <span class="font-semibold text-slate-700">Password strength</span>
              <span :class="passwordScore === 4 ? 'font-semibold text-emerald-700' : 'text-slate-500'">{{ passwordStrength }}</span>
            </div>
            <div role="meter" aria-label="Password strength" :aria-valuenow="passwordScore" aria-valuemin="0" aria-valuemax="4" :aria-valuetext="passwordStrength" class="mt-2 flex gap-1.5">
              <span v-for="level in 4" :key="level" class="h-1.5 flex-1 rounded-full transition-colors"
                :class="passwordScore >= level ? (passwordScore === 4 ? 'bg-emerald-500' : passwordScore >= 2 ? 'bg-amber-500' : 'bg-red-500') : 'bg-slate-200'"></span>
            </div>
            <ul class="mt-3 grid grid-cols-2 gap-x-4 gap-y-2">
              <li v-for="rule in passwordRules" :key="rule.label" class="flex items-center gap-2 text-xs"
                :class="rule.valid ? 'text-emerald-700' : 'text-slate-500'">
                <Check v-if="rule.valid" class="size-3.5 shrink-0" aria-hidden="true" />
                <span v-else class="size-3.5 shrink-0 rounded-full border border-current" aria-hidden="true"></span>
                <span>{{ rule.label }}</span>
              </li>
            </ul>
          </div>
          <div>
            <label for="account-role" class="mb-2 block text-sm font-medium text-slate-700">I’m joining as</label>
            <select id="account-role" v-model="form.role" required
              class="w-full rounded-lg border border-slate-300 bg-white px-3.5 py-3 outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-100">
              <option value="customer">Customer</option>
              <option value="mechanic">Mechanic</option>
            </select>
          </div>
          <p v-if="errorMessage" role="alert" class="rounded-lg bg-red-50 px-3.5 py-3 text-sm text-red-700 sm:col-span-2">{{ errorMessage }}</p>
          <div class="sm:col-span-2">
            <PrimaryButton type="submit" :loading="isSubmitting" class="w-full">Create account</PrimaryButton>
          </div>
        </form>

        <p class="mt-6 text-center text-sm text-slate-600">
          Already registered? <router-link to="/login" class="font-semibold text-blue-700 hover:text-blue-800">Sign in</router-link>
        </p>
      </div>
    </div>
  </section>
</template>
