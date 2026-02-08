<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { api } from '@/composables/useApi'

const auth = useAuthStore()
const router = useRouter()
const nickname = ref('')
const error = ref('')
const loading = ref(false)
const turnstileSiteKey = ref('')
const turnstileToken = ref('')
let turnstileWidgetId: string | null = null

const charCount = computed(() => nickname.value.length)

onMounted(async () => {
  try {
    const config = await api<{ turnstile_site_key: string }>('/api/auth/config')
    if (config.turnstile_site_key) {
      turnstileSiteKey.value = config.turnstile_site_key
      loadTurnstileScript()
    }
  } catch {
    // Config fetch failed; proceed without CAPTCHA
  }
})

function loadTurnstileScript() {
  if (document.querySelector('script[src*="turnstile"]')) {
    renderWidget()
    return
  }
  const script = document.createElement('script')
  script.src = 'https://challenges.cloudflare.com/turnstile/v0/api.js?onload=onTurnstileLoad'
  script.async = true
  ;(window as unknown as Record<string, () => void>).onTurnstileLoad = () => renderWidget()
  document.head.appendChild(script)
}

function renderWidget() {
  if (!window.turnstile || !turnstileSiteKey.value) return
  const container = document.getElementById('turnstile-widget')
  if (!container) return
  turnstileWidgetId = window.turnstile.render(container, {
    sitekey: turnstileSiteKey.value,
    callback: (token: string) => { turnstileToken.value = token },
    'error-callback': () => { turnstileToken.value = '' },
    'expired-callback': () => { turnstileToken.value = '' },
    theme: 'dark',
  })
}

function resetWidget() {
  turnstileToken.value = ''
  if (window.turnstile && turnstileWidgetId) {
    window.turnstile.reset(turnstileWidgetId)
  }
}

async function handleLogin() {
  error.value = ''
  if (nickname.value.length < 2 || nickname.value.length > 20) {
    error.value = 'ニックネームは2〜20文字で入力してください'
    return
  }
  if (turnstileSiteKey.value && !turnstileToken.value) {
    error.value = 'CAPTCHAの認証を完了してください'
    return
  }
  loading.value = true
  try {
    await auth.login(nickname.value, turnstileToken.value || undefined)
    router.push({ name: 'lobby' })
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'ログインに失敗しました'
    resetWidget()
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="flex items-center justify-center min-h-[70vh]">
    <div class="bg-gray-800 rounded-xl p-8 w-full max-w-sm shadow-2xl shadow-black/40 border border-gray-700/50 gm-animate-scale">
      <h1 class="text-2xl font-bold text-center mb-2 gm-gradient-text">Game Instant Matching</h1>
      <p class="text-gray-500 text-xs text-center mb-6">1戦だけ、すぐに遊ぼう</p>
      <p class="text-gray-400 text-sm text-center mb-6">
        ニックネームを入力してすぐに始めよう
      </p>
      <form @submit.prevent="handleLogin" class="space-y-4">
        <div class="relative">
          <input
            v-model="nickname"
            type="text"
            placeholder="ニックネーム"
            maxlength="20"
            class="w-full px-4 py-2.5 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500/30 transition-colors"
            autofocus
          />
          <span
            v-if="charCount > 0"
            class="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-gray-500"
          >
            {{ charCount }}/20
          </span>
        </div>
        <div v-if="turnstileSiteKey" id="turnstile-widget" class="flex justify-center"></div>
        <p v-if="error" class="text-red-400 text-sm">{{ error }}</p>
        <button
          type="submit"
          :disabled="loading"
          class="w-full py-2.5 bg-gradient-to-r from-cyan-600 to-indigo-600 hover:from-cyan-500 hover:to-indigo-500 disabled:opacity-50 rounded-lg font-medium transition-all shadow-lg shadow-indigo-500/20 flex items-center justify-center gap-2"
        >
          <span v-if="loading" class="gm-spinner"></span>
          {{ loading ? 'ログイン中...' : 'はじめる' }}
        </button>
      </form>
    </div>
  </div>
</template>
