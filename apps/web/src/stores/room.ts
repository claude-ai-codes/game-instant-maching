import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Room, Message } from '@/types'
import { api } from '@/composables/useApi'

export const useRoomStore = defineStore('room', () => {
  const room = ref<Room | null>(null)
  const messages = ref<Message[]>([])

  async function fetchRoom(id: string) {
    room.value = await api<Room>('/api/rooms/' + id)
  }

  async function fetchMessages(roomId: string) {
    messages.value = await api<Message[]>('/api/rooms/' + roomId + '/messages')
  }

  async function sendMessage(roomId: string, content: string) {
    await api('/api/rooms/' + roomId + '/messages', {
      method: 'POST',
      body: JSON.stringify({ content }),
    })
    await fetchMessages(roomId)
  }

  async function closeRoom(roomId: string) {
    await api('/api/rooms/' + roomId + '/close', { method: 'POST' })
    await fetchRoom(roomId)
  }

  async function submitFeedback(roomId: string, toUserId: string, rating: 'thumbs_up' | 'thumbs_down') {
    await api('/api/rooms/' + roomId + '/feedback', {
      method: 'POST',
      body: JSON.stringify({ to_user_id: toUserId, rating }),
    })
  }

  return { room, messages, fetchRoom, fetchMessages, sendMessage, closeRoom, submitFeedback }
})
