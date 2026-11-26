<script setup>
</script>

<template>
  <div class="min-h-screen bg-slate-950 text-white">
    <header class="sticky top-0 z-40 border-b border-white/10 bg-slate-950/85 backdrop-blur-xl">
      <nav class="mx-auto flex h-[4.5rem] max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8" aria-label="Public navigation">
        <router-link to="/" class="group flex items-center gap-3" aria-label="Fixer AI home">
          <span class="grid size-10 place-items-center rounded-2xl bg-primary text-lg font-black text-white shadow-lg shadow-blue-500/20 transition duration-300 group-hover:rotate-6 group-hover:scale-105">F</span>
          <span class="text-lg font-bold tracking-tight">Fixer <span class="text-blue-300">AI</span></span>
        </router-link>
        <div class="flex items-center gap-3 text-sm font-semibold sm:gap-6">
          <router-link to="/login" class="text-slate-300 transition hover:text-white">Sign in</router-link>
          <router-link to="/register" class="rounded-xl bg-white px-4 py-2.5 text-slate-950 shadow-lg shadow-black/10 transition hover:-translate-y-0.5 hover:bg-blue-100">Get started</router-link>
        </div>
      </nav>
    </header>
    <main><router-view /></main>
    <footer class="border-t border-white/10 px-4 py-6 text-center text-xs text-slate-500">Fixer AI · Local help for the road ahead</footer>
  </div>
</template>
