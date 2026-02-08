import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Recruitment } from '@/types'
import { api } from '@/composables/useApi'

export const useRecruitmentStore = defineStore('recruitment', () => {
  const recruitments = ref<Recruitment[]>([])
  const loading = ref(false)

  async function fetchRecruitments() {
    recruitments.value = await api<Recruitment[]>('/api/recruitments')
  }

  async function createRecruitment(data: {
    game: string
    region: string
    start_time: string
    desired_role?: string
    memo?: string
    play_style?: string
    has_microphone?: boolean
  }): Promise<Recruitment> {
    loading.value = true
    try {
      const r = await api<Recruitment>('/api/recruitments', {
        method: 'POST',
        body: JSON.stringify(data),
      })
      return r
    } finally {
      loading.value = false
    }
  }

  async function joinRecruitment(id: string): Promise<{ detail: string; room_id: string }> {
    return api('/api/recruitments/' + id + '/join', { method: 'POST' })
  }

  async function cancelRecruitment(id: string) {
    await api('/api/recruitments/' + id, { method: 'DELETE' })
    await fetchRecruitments()
  }

  return { recruitments, loading, fetchRecruitments, createRecruitment, joinRecruitment, cancelRecruitment }
})
