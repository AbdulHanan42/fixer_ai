<script setup>
</script>

<template>
  <div class="min-h-screen bg-slate-50 text-slate-900">
    <header class="border-b border-slate-200 bg-white">
      <nav class="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        <router-link to="/" class="flex items-center gap-3" aria-label="Fixer AI home">
          <span class="grid size-9 place-items-center rounded-xl bg-blue-600 font-black text-white">F</span>
          <span class="text-lg font-bold tracking-tight">Fixer AI</span>
        </router-link>
        <div class="flex items-center gap-3 text-sm font-semibold sm:gap-5">
          <router-link to="/" class="hidden text-slate-600 hover:text-blue-700 sm:inline">Home</router-link>
          <router-link to="/login" class="text-slate-600 hover:text-blue-700">Sign in</router-link>
          <router-link to="/register" class="rounded-lg bg-blue-600 px-3 py-2 text-white hover:bg-blue-700">Create account</router-link>
        </div>
      </nav>
    </header>
    <main>
      <router-view />
    </main>
  </div>
</template>
