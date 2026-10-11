<script setup>
</script>

<template>
  <div class="min-h-screen bg-gray-50">
    <nav class="bg-white shadow-sm">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between h-16">
          <div class="flex items-center">
            <span class="text-xl font-bold text-gray-900">Fixer AI</span>
          </div>
          <div class="flex items-center space-x-4">
            <router-link to="/" class="text-gray-700 hover:text-gray-900">Home</router-link>
            <router-link to="/login" class="text-gray-700 hover:text-gray-900">Login</router-link>
            <router-link to="/register" class="text-gray-700 hover:text-gray-900">Register</router-link>
          </div>
        </div>
      </div>
    </nav>
    <main>
      <router-view />
    </main>
  </div>
</template>
