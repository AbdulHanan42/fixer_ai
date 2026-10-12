<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import PrimaryButton from '@/components/ui/PrimaryButton.vue'
import { useNotifications } from '@/composables/useNotifications.js'
import { authService } from '@/services/auth.service.js'

const router = useRouter()
const { showSuccess } = useNotifications()
const form = reactive({ full_name: '', email: '', phone_number: '', password: '', role: 'customer' })
const errorMessage = ref('')
const isSubmitting = ref(false)

async function submitRegistration() {
  errorMessage.value = ''
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
  <section class="mx-auto max-w-lg px-4 py-10 sm:py-14">
    <div class="rounded-2xl border border-slate-200 bg-white p-7 shadow-sm sm:p-9">
      <p class="text-sm font-semibold uppercase tracking-wider text-blue-600">Get started</p>
      <h1 class="mt-2 text-3xl font-bold tracking-tight text-slate-900">Create your account</h1>
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
        <div>
          <label for="register-password" class="mb-2 block text-sm font-medium text-slate-700">Password</label>
          <input id="register-password" v-model="form.password" type="password" autocomplete="new-password" minlength="8" maxlength="100" required
            class="w-full rounded-lg border border-slate-300 px-3.5 py-3 outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-100" />
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
  </section>
</template>
