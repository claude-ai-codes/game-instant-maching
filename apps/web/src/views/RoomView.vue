<script setup lang="ts">
import { ref, computed, nextTick, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useRoomStore } from '@/stores/room'
import { useAuthStore } from '@/stores/auth'
import { useWebSocket } from '@/composables/useWebSocket'
import { gameName, regionName } from '@/utils/data'

const route = useRoute()
const router = useRouter()
const roomStore = useRoomStore()
const auth = useAuthStore()
const roomId = route.params.id as string

const newMessage = ref('')
const error = ref('')
const chatContainer = ref<HTMLElement | null>(null)
let pollTimer: ReturnType<typeof setInterval> | null = null

const otherMember = computed(() => {
  return roomStore.room?.members.find(m => m.user_id !== auth.user?.id)
})

const myMember = computed(() => {
  return roomStore.room?.members.find(m => m.user_id === auth.user?.id)
})

const pendingClose = computed(() => {
  return myMember.value?.ready_to_close === true && roomStore.room?.status === 'active'
})

// WebSocket for real-time updates
const { on } = useWebSocket()

on('new_message', async (data) => {
  if (data.room_id === roomId) {
    await roomStore.fetchMessages(roomId)
    scrollToBottom()
  }
})

on('room_closed', async (data) => {
  if (data.room_id === roomId) {
    await roomStore.fetchRoom(roomId)
  }
})

on('close_requested', async (data) => {
  if (data.room_id === roomId) {
    await roomStore.fetchRoom(roomId)
  }
})

onMounted(async () => {
  await roomStore.fetchRoom(roomId)
  await roomStore.fetchMessages(roomId)
  scrollToBottom()
  // Slower fallback polling with WS active
  pollTimer = setInterval(async () => {
    await roomStore.fetchMessages(roomId)
    await roomStore.fetchRoom(roomId)
  }, 10000)
})

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
})

function scrollToBottom() {
  nextTick(() => {
    if (chatContainer.value) {
      chatContainer.value.scrollTop = chatContainer.value.scrollHeight
    }
  })
}

async function send() {
  if (!newMessage.value.trim()) return
  error.value = ''
  try {
    await roomStore.sendMessage(roomId, newMessage.value.trim())
    newMessage.value = ''
    scrollToBottom()
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : '送信に失敗しました'
  }
}

async function handleClose() {
  if (!confirm('ルームを閉じますか？（1戦終了後に閉じてください）')) return
  try {
    const result = await roomStore.closeRoom(roomId)
    if (result?.status === 'closed') {
      router.push({ name: 'feedback', params: { id: roomId } })
    } else {
      // Refetch room to update ready_to_close states
      await roomStore.fetchRoom(roomId)
    }
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'クローズに失敗しました'
  }
}

function formatTime(iso: string) {
  return new Date(iso).toLocaleTimeString('ja-JP', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}
</script>

<template>
  <div v-if="roomStore.room">
    <div class="flex items-center justify-between mb-4">
      <div>
        <h1 class="text-lg font-bold">
          {{ gameName(roomStore.room.game ?? '') }} · {{ regionName(roomStore.room.region ?? '') }}
        </h1>
        <p class="text-sm text-gray-400">
          メンバー: {{ roomStore.room.members.map(m => m.nickname).join(', ') }}
        </p>
      </div>
      <div class="flex items-center gap-2">
        <span
          class="text-xs px-2 py-1 rounded"
          :class="{
            'bg-green-800 text-green-200': roomStore.room.status === 'active',
            'bg-gray-700 text-gray-400': roomStore.room.status !== 'active',
          }"
        >
          {{ roomStore.room.status === 'active' ? 'アクティブ' : 'クローズ済み' }}
        </span>
        <span
          v-if="pendingClose"
          class="text-xs px-2 py-1 rounded bg-yellow-800 text-yellow-200"
        >
          相手の同意を待っています...
        </span>
        <button
          v-else-if="roomStore.room.status === 'active'"
          @click="handleClose"
          class="px-3 py-1 bg-red-600 hover:bg-red-700 rounded text-sm transition"
        >
          ルームを閉じる
        </button>
        <router-link
          v-if="roomStore.room.status !== 'active'"
          :to="{ name: 'feedback', params: { id: roomId } }"
          class="px-3 py-1 bg-blue-600 hover:bg-blue-700 rounded text-sm transition"
        >
          フィードバック
        </router-link>
      </div>
    </div>

    <!-- Chat -->
    <div
      ref="chatContainer"
      class="bg-gray-800 rounded-lg border border-gray-700 h-96 overflow-y-auto p-4 space-y-2 mb-4"
    >
      <div v-if="roomStore.messages.length === 0" class="text-center text-gray-500 py-8">
        まだメッセージがありません
      </div>
      <div
        v-for="msg in roomStore.messages"
        :key="msg.id"
        class="flex flex-col"
        :class="msg.user_id === auth.user?.id ? 'items-end' : 'items-start'"
      >
        <span class="text-xs text-gray-500 mb-0.5">{{ msg.nickname }} · {{ formatTime(msg.created_at) }}</span>
        <div
          class="max-w-xs px-3 py-2 rounded-lg text-sm"
          :class="msg.user_id === auth.user?.id ? 'bg-blue-700' : 'bg-gray-700'"
        >
          {{ msg.content }}
        </div>
      </div>
    </div>

    <p v-if="error" class="text-red-400 text-sm mb-2">{{ error }}</p>

    <form
      v-if="roomStore.room.status === 'active'"
      @submit.prevent="send"
      class="flex gap-2"
    >
      <input
        v-model="newMessage"
        type="text"
        maxlength="500"
        placeholder="メッセージを入力..."
        class="flex-1 px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
      />
      <button
        type="submit"
        :disabled="!newMessage.trim()"
        class="px-6 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 rounded-lg font-medium transition"
      >
        送信
      </button>
    </form>
  </div>
  <div v-else class="text-center text-gray-500 py-12">ルームを読み込み中...</div>
</template>
