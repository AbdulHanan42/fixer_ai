<script setup>
</script>

<template>
  <div class="overflow-hidden">
    <section class="relative isolate mx-auto grid min-h-[min(760px,calc(100svh-4.5rem))] max-w-7xl items-center gap-10 px-4 py-16 sm:px-6 sm:py-20 lg:grid-cols-[1.05fr_.95fr] lg:px-8 lg:py-24">
      <div class="pointer-events-none absolute -left-40 top-10 -z-10 size-[32rem] rounded-full bg-blue-600/20 blur-[100px]"></div>
      <div class="pointer-events-none absolute right-0 top-24 -z-10 size-80 rounded-full bg-cyan-400/10 blur-[90px]"></div>
      <div class="relative">
        <div class="inline-flex items-center gap-2 rounded-full border border-cyan-200/20 bg-cyan-100/[.06] px-3 py-1.5 text-xs font-bold text-cyan-200"><span class="size-1.5 animate-pulse rounded-full bg-cyan-300"></span> Your local repair connection</div>
        <h1 class="mt-6 max-w-3xl text-5xl font-black leading-[1.03] tracking-[-.055em] sm:text-6xl lg:text-7xl">Car trouble?<br /><span class="bg-gradient-to-r from-cyan-200 via-blue-300 to-indigo-300 bg-clip-text text-transparent">Find your way forward.</span></h1>
        <p class="mt-6 max-w-xl text-base leading-7 text-slate-300 sm:text-lg sm:leading-8">Describe what is happening, find nearby mechanics, and keep every repair conversation and update in one place.</p>
        <div class="mt-8 flex flex-col gap-3 sm:flex-row">
          <router-link to="/register" class="inline-flex items-center justify-center gap-2 rounded-2xl bg-gradient-to-r from-cyan-300 to-blue-400 px-6 py-3.5 text-sm font-black text-slate-950 shadow-xl shadow-blue-950/40 transition duration-300 hover:-translate-y-1 hover:shadow-cyan-400/20">Find a mechanic <span aria-hidden="true">→</span></router-link>
          <router-link to="/register" class="inline-flex items-center justify-center rounded-2xl border border-white/15 bg-white/[.04] px-6 py-3.5 text-sm font-bold text-white transition hover:bg-white/[.09]">Join as a mechanic</router-link>
        </div>
        <p class="mt-4 text-xs text-slate-500">No payment required to create an account.</p>
      </div>

      <div class="relative mx-auto w-full max-w-lg [perspective:1200px]">
        <div class="absolute -inset-8 rounded-[3rem] bg-gradient-to-br from-blue-500/20 to-cyan-300/10 blur-3xl"></div>
        <div class="relative rounded-[2rem] border border-white/15 bg-gradient-to-br from-white/[.12] to-white/[.035] p-3 shadow-2xl shadow-black/40 transition duration-700 hover:[transform:rotateY(-4deg)_rotateX(3deg)]">
          <div class="rounded-[1.5rem] border border-white/10 bg-slate-900/90 p-5 sm:p-6">
            <div class="flex items-center justify-between"><div><p class="text-[10px] font-bold uppercase tracking-[.2em] text-cyan-300">Your repair journey</p><p class="mt-1 text-lg font-bold">From problem to repair</p></div><div class="grid size-11 place-items-center rounded-2xl bg-blue-500/15 text-xl text-blue-200">✦</div></div>
            <div class="mt-6 space-y-3">
              <div class="flex items-center gap-4 rounded-2xl border border-white/10 bg-white/[.045] p-4"><span class="grid size-9 shrink-0 place-items-center rounded-xl bg-cyan-300/15 text-sm font-black text-cyan-200">01</span><div><p class="text-sm font-bold">Describe the issue</p><p class="mt-0.5 text-xs text-slate-400">Add your vehicle and location</p></div><span class="ml-auto text-cyan-300">✓</span></div>
              <div class="flex items-center gap-4 rounded-2xl border border-blue-300/25 bg-blue-500/10 p-4 shadow-lg shadow-blue-950/20"><span class="grid size-9 shrink-0 place-items-center rounded-xl bg-blue-300/20 text-sm font-black text-blue-100">02</span><div><p class="text-sm font-bold">Connect nearby</p><p class="mt-0.5 text-xs text-slate-400">Compare available local shops</p></div><span class="ml-auto size-2 animate-pulse rounded-full bg-cyan-300"></span></div>
              <div class="flex items-center gap-4 rounded-2xl border border-white/10 bg-white/[.045] p-4"><span class="grid size-9 shrink-0 place-items-center rounded-xl bg-indigo-300/15 text-sm font-black text-indigo-200">03</span><div><p class="text-sm font-bold">Stay in the loop</p><p class="mt-0.5 text-xs text-slate-400">Chat and follow repair updates</p></div><span class="ml-auto text-slate-500">···</span></div>
            </div>
            <div class="mt-5 flex items-center justify-between rounded-xl bg-slate-950/70 px-4 py-3"><span class="text-xs text-slate-400">Your workspace</span><span class="flex items-center gap-2 text-xs font-semibold text-emerald-300"><span class="size-1.5 rounded-full bg-emerald-400"></span>Ready when you are</span></div>
          </div>
        </div>
        <div class="absolute -bottom-5 -left-5 hidden items-center gap-3 rounded-2xl border border-white/15 bg-slate-800/95 p-3 shadow-xl sm:flex"><span class="grid size-10 place-items-center rounded-xl bg-emerald-400/15 text-emerald-300">✓</span><span><span class="block text-xs font-bold">Verified shops</span><span class="mt-0.5 block text-[10px] text-slate-400">Trust starts with clear details</span></span></div>
      </div>
    </section>

    <section class="border-y border-white/[.08] bg-white/[.025]">
      <div class="mx-auto grid max-w-7xl gap-4 px-4 py-14 sm:grid-cols-3 sm:px-6 lg:px-8">
        <article class="rounded-2xl border border-white/10 bg-slate-900/60 p-5 transition duration-300 hover:-translate-y-1 hover:border-blue-300/25"><span class="text-xs font-bold text-cyan-300">01 / DISCOVER</span><h2 class="mt-3 text-lg font-bold">Nearby, with context</h2><p class="mt-2 text-sm leading-6 text-slate-400">Search available mechanics around your location and review shop details before you send a request.</p></article>
        <article class="rounded-2xl border border-white/10 bg-slate-900/60 p-5 transition duration-300 hover:-translate-y-1 hover:border-blue-300/25"><span class="text-xs font-bold text-cyan-300">02 / COORDINATE</span><h2 class="mt-3 text-lg font-bold">One repair conversation</h2><p class="mt-2 text-sm leading-6 text-slate-400">Keep messages attached to the repair request so both sides can stay on the same page.</p></article>
        <article class="rounded-2xl border border-white/10 bg-slate-900/60 p-5 transition duration-300 hover:-translate-y-1 hover:border-blue-300/25"><span class="text-xs font-bold text-cyan-300">03 / COMPLETE</span><h2 class="mt-3 text-lg font-bold">Follow every update</h2><p class="mt-2 text-sm leading-6 text-slate-400">See request status changes and share feedback after your repair is complete.</p></article>
      </div>
    </section>
    <section class="mx-auto flex max-w-7xl flex-col items-start justify-between gap-5 px-4 py-14 sm:px-6 md:flex-row md:items-center lg:px-8">
      <div><h2 class="text-2xl font-black tracking-tight sm:text-3xl">Get back to what moves you.</h2><p class="mt-2 text-sm text-slate-400">Create your Fixer AI account and get started.</p></div>
      <router-link to="/register" class="rounded-xl bg-white px-5 py-3 text-sm font-black text-slate-950 transition hover:-translate-y-0.5 hover:bg-blue-100">Create free account <span aria-hidden="true">→</span></router-link>
    </section>
  </div>
</template>
