<script setup>
import { useAuthStore } from '@/stores/auth.js'

const auth = useAuthStore()
const homePath = auth.isMechanic ? '/mechanic/dashboard' : auth.isAdmin ? '/admin/dashboard' : auth.isCustomer ? '/customer/dashboard' : '/'
</script>

<template>
  <main class="grid min-h-[70vh] place-items-center px-4 py-16">
    <section class="w-full max-w-lg rounded-3xl border border-slate-200 bg-white p-8 text-center shadow-xl shadow-slate-900/5 sm:p-12">
      <span class="mx-auto grid size-16 place-items-center rounded-2xl bg-blue-50 text-2xl font-black text-blue-700">404</span>
      <p class="mt-6 text-xs font-bold uppercase tracking-[.2em] text-blue-700">Wrong turn</p>
      <h1 class="mt-2 text-3xl font-black tracking-tight text-slate-950">This page is off the map.</h1>
      <p class="mx-auto mt-3 max-w-sm text-sm leading-6 text-slate-500">The address may have changed, or this page may no longer be available.</p>
      <router-link :to="homePath" class="mt-7 inline-flex items-center gap-2 rounded-xl bg-slate-950 px-5 py-3 text-sm font-bold text-white transition hover:-translate-y-0.5 hover:bg-blue-700">Back to Fixer AI <span aria-hidden="true">→</span></router-link>
    </section>
  </main>
</template>
