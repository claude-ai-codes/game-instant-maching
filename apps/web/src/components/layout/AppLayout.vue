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
    <header class="bg-gray-800 border-b border-gray-700">
      <div class="max-w-4xl mx-auto px-4 py-3 flex items-center justify-between">
        <router-link to="/lobby" class="text-lg font-bold text-blue-400 hover:text-blue-300">
          Game Instant Matching
        </router-link>
        <div v-if="auth.user" class="flex items-center gap-4">
          <span class="text-sm text-gray-400">{{ auth.user.nickname }}</span>
          <button
            @click="handleLogout"
            class="text-sm text-gray-400 hover:text-white"
          >
            ログアウト
          </button>
        </div>
      </div>
    </header>
    <main class="max-w-4xl mx-auto px-4 py-6">
      <slot />
    </main>
  </div>
</template>
