import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { User } from '@/types'
import { api } from '@/composables/useApi'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)

  async function login(nickname: string) {
    user.value = await api<User>('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ nickname }),
    })
  }

  async function logout() {
    await api('/api/auth/logout', { method: 'POST' })
    user.value = null
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
