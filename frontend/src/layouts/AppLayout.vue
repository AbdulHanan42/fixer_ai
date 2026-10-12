<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth.js'
import NotificationCenter from '@/components/notifications/NotificationCenter.vue'

const auth = useAuthStore()
const route = useRoute()
const mobileOpen = ref(false)
const links = computed(() => auth.isMechanic
  ? [{ label: 'Overview', to: '/mechanic/dashboard', icon: '▦' }]
  : auth.isAdmin
    ? [{ label: 'Overview', to: '/admin/dashboard', icon: '▦' }]
    : [{ label: 'Find a mechanic', to: '/customer/dashboard', icon: '⌖' }])
const userName = computed(() => auth.user?.full_name || auth.user?.email || 'Your account')
const roleLabel = computed(() => auth.user?.role ? `${auth.user.role[0].toUpperCase()}${auth.user.role.slice(1)} account` : 'Fixer AI member')

watch(() => route.fullPath, () => { mobileOpen.value = false })
</script>

<template>
  <div class="min-h-screen bg-slate-50 text-slate-900">
    <button v-if="mobileOpen" type="button" class="fixed inset-0 z-40 bg-slate-950/45 backdrop-blur-sm lg:hidden" aria-label="Close navigation" @click="mobileOpen = false"></button>
    <aside :class="mobileOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'" class="fixed inset-y-0 left-0 z-50 flex w-[min(19rem,85vw)] flex-col border-r border-white/10 bg-slate-950 px-5 py-6 text-white shadow-2xl transition-transform duration-300 lg:w-72 lg:translate-x-0">
      <div class="pointer-events-none absolute -right-16 top-20 size-48 rounded-full bg-blue-500/20 blur-3xl"></div>
      <div class="relative flex items-center justify-between">
        <router-link to="/" class="group flex items-center gap-3" aria-label="Fixer AI home">
          <span class="grid size-11 place-items-center rounded-2xl bg-gradient-to-br from-blue-400 to-indigo-600 text-xl font-black shadow-lg shadow-blue-900/50 transition duration-500 group-hover:rotate-6 group-hover:scale-110">F</span>
          <span><span class="block text-lg font-bold tracking-tight">Fixer AI</span><span class="block text-[10px] uppercase tracking-[.25em] text-slate-400">Mobility, made easier</span></span>
        </router-link>
        <button class="rounded-lg p-2 text-slate-400 hover:bg-white/10 lg:hidden" aria-label="Close navigation" @click="mobileOpen = false">✕</button>
      </div>

      <div class="relative mt-10 rounded-2xl border border-white/10 bg-white/[.06] p-4 shadow-xl shadow-black/10 [transform:perspective(900px)_rotateY(2deg)]">
        <div class="flex items-center gap-3">
          <div class="grid size-11 shrink-0 place-items-center rounded-full bg-gradient-to-br from-cyan-300 to-blue-500 text-sm font-bold text-slate-950">{{ userName.slice(0, 1).toUpperCase() }}</div>
          <div class="min-w-0"><p class="truncate text-sm font-semibold">{{ userName }}</p><p class="mt-0.5 text-xs capitalize text-slate-400">{{ roleLabel }}</p></div>
        </div>
        <div class="mt-4 flex items-center gap-2 text-[11px] font-medium text-emerald-300"><span class="size-1.5 animate-pulse rounded-full bg-emerald-400"></span>Account protected</div>
      </div>

      <p class="mb-3 mt-9 px-3 text-[10px] font-bold uppercase tracking-[.22em] text-slate-500">Workspace</p>
      <nav class="relative space-y-1.5" aria-label="Main navigation">
        <router-link v-for="link in links" :key="link.to" :to="link.to" class="group flex items-center gap-3 rounded-xl px-3 py-3 text-sm font-semibold text-slate-400 transition duration-200 hover:translate-x-1 hover:bg-white/[.07] hover:text-white" active-class="!translate-x-1 !bg-blue-500/15 !text-blue-200 ring-1 ring-blue-400/20">
          <span class="grid size-8 place-items-center rounded-lg bg-white/[.05] text-lg transition group-hover:bg-blue-400/15">{{ link.icon }}</span>{{ link.label }}
          <span class="ml-auto text-xs opacity-0 transition group-hover:opacity-100">→</span>
        </router-link>
      </nav>
      <NotificationCenter />

      <div class="relative mt-auto rounded-2xl border border-blue-400/15 bg-gradient-to-br from-blue-500/15 to-indigo-500/5 p-4">
        <p class="text-sm font-semibold">Need a hand?</p><p class="mt-1 text-xs leading-5 text-slate-400">Your vehicle support is right around the corner.</p>
        <div class="mt-3 h-1 overflow-hidden rounded-full bg-white/10"><div class="h-full w-2/3 animate-pulse rounded-full bg-gradient-to-r from-cyan-300 to-blue-500"></div></div>
      </div>
      <button type="button" class="mt-5 flex items-center gap-3 rounded-xl px-3 py-3 text-sm font-semibold text-slate-400 transition hover:bg-rose-400/10 hover:text-rose-200" @click="auth.logout()"><span class="grid size-8 place-items-center rounded-lg bg-white/[.05]">↪</span>Sign out</button>
      <p class="mt-4 px-3 text-[10px] text-slate-600">© 2025 Fixer AI</p>
    </aside>

    <div class="min-h-screen lg:pl-72">
      <div class="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-slate-200/70 bg-white/80 px-4 backdrop-blur-xl sm:px-8 lg:hidden">
        <button type="button" class="grid size-10 place-items-center rounded-xl border border-slate-200 bg-white text-lg shadow-sm" aria-label="Open navigation" @click="mobileOpen = true">☰</button>
        <span class="font-bold tracking-tight">Fixer <span class="text-blue-600">AI</span></span>
        <div class="grid size-9 place-items-center rounded-full bg-blue-100 text-xs font-bold text-blue-800">{{ userName.slice(0, 1).toUpperCase() }}</div>
      </div>
      <main class="relative min-h-screen overflow-hidden px-4 py-7 sm:px-8 sm:py-10 lg:px-10">
        <div class="pointer-events-none absolute -right-32 -top-32 size-96 rounded-full bg-blue-200/30 blur-3xl"></div>
        <div class="pointer-events-none absolute -bottom-40 left-1/3 size-96 rounded-full bg-indigo-100/40 blur-3xl"></div>
        <div class="relative mx-auto max-w-[1500px]">
          <router-view />
        </div>
      </main>
    </div>
  </div>
</template>
