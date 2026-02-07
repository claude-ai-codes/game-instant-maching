<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()
const nickname = ref('')
const error = ref('')

async function handleLogin() {
  error.value = ''
  if (nickname.value.length < 2 || nickname.value.length > 20) {
    error.value = 'ニックネームは2〜20文字で入力してください'
    return
  }
  try {
    await auth.login(nickname.value)
    router.push({ name: 'lobby' })
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'ログインに失敗しました'
  }
}
</script>

<template>
  <div class="flex items-center justify-center min-h-[70vh]">
    <div class="bg-gray-800 rounded-lg p-8 w-full max-w-sm shadow-lg">
      <h1 class="text-2xl font-bold text-center mb-6 text-blue-400">Game Instant Matching</h1>
      <p class="text-gray-400 text-sm text-center mb-6">
        ニックネームを入力してすぐに始めよう
      </p>
      <form @submit.prevent="handleLogin" class="space-y-4">
        <div>
          <input
            v-model="nickname"
            type="text"
            placeholder="ニックネーム"
            maxlength="20"
            class="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
            autofocus
          />
        </div>
        <p v-if="error" class="text-red-400 text-sm">{{ error }}</p>
        <button
          type="submit"
          class="w-full py-2 bg-blue-600 hover:bg-blue-700 rounded-lg font-medium transition"
        >
          はじめる
        </button>
      </form>
    </div>
  </div>
</template>
