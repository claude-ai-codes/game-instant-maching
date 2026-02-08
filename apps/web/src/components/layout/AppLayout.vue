<script setup lang="ts">
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'

const auth = useAuthStore()
const router = useRouter()

async function handleLogout() {
  await auth.logout()
  router.push({ name: 'login' })
}
</script>

<template>
  <div class="min-h-screen bg-gray-900 text-gray-100">
    <!-- Gradient accent line -->
    <div class="h-0.5 bg-gradient-to-r from-cyan-500 via-indigo-500 to-violet-500"></div>

    <header class="bg-gray-800/80 backdrop-blur-sm border-b border-gray-700/50 shadow-lg shadow-black/20">
      <div class="max-w-4xl mx-auto px-4 py-3 flex items-center justify-between">
        <router-link to="/lobby" class="text-lg font-bold gm-gradient-text hover:opacity-80 transition-opacity">
          Game Instant Matching
        </router-link>
        <div v-if="auth.user" class="flex items-center gap-4">
          <span class="text-sm text-gray-400 flex items-center gap-1.5">
            <span class="w-2 h-2 rounded-full bg-green-500 shadow-sm shadow-green-500/50 inline-block"></span>
            {{ auth.user.nickname }}
          </span>
          <button
            @click="handleLogout"
            class="text-sm text-gray-400 hover:text-white transition-colors"
          >
            ログアウト
          </button>
        </div>
      </div>
    </header>
    <main class="max-w-4xl mx-auto px-4 py-6 gm-animate-page">
      <slot />
    </main>
  </div>
</template>
