import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { User } from '@/types'
import { api } from '@/composables/useApi'
import { useRecruitmentStore } from '@/stores/recruitment'
import { useRoomStore } from '@/stores/room'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)

  async function login(nickname: string, turnstileToken?: string) {
    const payload: Record<string, string> = { nickname }
    if (turnstileToken) {
      payload.turnstile_token = turnstileToken
    }
    user.value = await api<User>('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  }

  async function logout() {
    await api('/api/auth/logout', { method: 'POST' })
    user.value = null
    const recruitmentStore = useRecruitmentStore()
    const roomStore = useRoomStore()
    recruitmentStore.recruitments = []
    recruitmentStore.loading = false
    roomStore.room = null
    roomStore.messages = []
  }

  async function fetchMe() {
    try {
      user.value = await api<User>('/api/auth/me')
    } catch {
      user.value = null
    }
  }

  return { user, login, logout, fetchMe }
})
