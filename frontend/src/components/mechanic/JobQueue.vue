<script setup>
import PrimaryButton from '@/components/ui/PrimaryButton.vue'
import StatusBadge from '@/components/ui/StatusBadge.vue'

defineProps({
  requests: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
  busyRequestId: { type: String, default: '' },
  error: { type: String, default: '' },
  actionsDisabled: { type: Boolean, default: false },
})

defineEmits(['update-status', 'refresh'])
</script>

<template>
  <section class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div>
        <p class="text-sm font-semibold uppercase tracking-wider text-blue-600">Work queue</p>
        <h2 class="mt-1 text-xl font-bold">Incoming repair requests</h2>
        <p class="mt-1 text-sm text-slate-600">Accept a job to assign it to your shop, or reject it if you can’t take it.</p>
      </div>
      <div class="flex items-center gap-3">
        <span class="rounded-full bg-amber-50 px-3 py-1 text-sm font-semibold text-amber-800">{{ requests.length }} pending</span>
        <button type="button" class="rounded-lg border border-slate-300 px-3 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50"
          :disabled="loading" @click="$emit('refresh')">Refresh</button>
      </div>
    </div>

    <p v-if="actionsDisabled" class="mt-4 rounded-lg bg-amber-50 px-4 py-3 text-sm text-amber-900">
      Go online to accept or reject incoming requests.
    </p>

    <p v-if="error" role="alert" class="mt-5 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">{{ error }}</p>

    <div v-if="loading" class="mt-6 grid min-h-40 place-items-center rounded-xl bg-slate-50 text-sm text-slate-600" role="status">
      Loading repair requests...
    </div>
    <div v-else-if="requests.length" class="mt-6 space-y-4">
      <article v-for="request in requests" :key="request.id" class="rounded-xl border border-slate-200 p-5 transition hover:border-blue-200">
        <div class="flex flex-wrap items-start justify-between gap-4">
          <div class="min-w-0 flex-1">
            <div class="flex flex-wrap items-center gap-2">
              <h3 class="font-bold text-slate-900">Request #{{ request.id.slice(0, 8) }}</h3>
              <StatusBadge :status="request.status" />
            </div>
            <p class="mt-3 whitespace-pre-line text-sm leading-6 text-slate-700">{{ request.description }}</p>
            <p class="mt-3 text-xs text-slate-500">
              {{ request.created_at ? new Date(request.created_at).toLocaleString() : 'Recently submitted' }}
              <span v-if="request.latitude != null && request.longitude != null"> · Location attached</span>
            </p>
          </div>
          <div class="flex w-full gap-2 sm:w-auto">
            <PrimaryButton variant="secondary" :disabled="actionsDisabled || Boolean(busyRequestId)" @click="$emit('update-status', request, 'cancelled')">
              {{ busyRequestId === request.id ? 'Updating...' : 'Reject' }}
            </PrimaryButton>
            <PrimaryButton :disabled="actionsDisabled || Boolean(busyRequestId)" @click="$emit('update-status', request, 'accepted')">
              {{ busyRequestId === request.id ? 'Updating...' : 'Accept job' }}
            </PrimaryButton>
          </div>
        </div>
      </article>
    </div>
    <div v-else-if="!error" class="mt-6 grid min-h-48 place-items-center rounded-xl border border-dashed border-slate-300 bg-slate-50 p-6 text-center">
      <div>
        <span class="mx-auto grid size-12 place-items-center rounded-full bg-white text-xl text-slate-500 shadow-sm" aria-hidden="true">⌁</span>
        <p class="mt-3 font-semibold text-slate-800">No pending jobs</p>
        <p class="mt-1 text-sm text-slate-500">New requests will appear here when customers need help.</p>
      </div>
    </div>
  </section>
</template>
