<script setup lang="ts">
import { ref, computed, nextTick, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useRoomStore } from '@/stores/room'
import { useAuthStore } from '@/stores/auth'
import { useWebSocket } from '@/composables/useWebSocket'
import { useGameStore } from '@/stores/game'
import { regionName } from '@/utils/data'

const route = useRoute()
const router = useRouter()
const roomStore = useRoomStore()
const auth = useAuthStore()
const gameStore = useGameStore()
const roomId = route.params.id as string

const newMessage = ref('')
const error = ref('')
const chatContainer = ref<HTMLElement | null>(null)
let pollTimer: ReturnType<typeof setInterval> | null = null

const msgCharCount = computed(() => newMessage.value.length)

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
  gameStore.fetchGames()
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
    <!-- Room header card -->
    <div class="bg-gray-800/60 rounded-xl border border-gray-700/50 p-4 mb-4 shadow-lg shadow-black/10">
      <div class="flex items-center justify-between">
        <div>
          <h1 class="text-lg font-bold">
            {{ gameStore.gameName(roomStore.room.game ?? '') }} · {{ regionName(roomStore.room.region ?? '') }}
          </h1>
          <p class="text-sm text-gray-400">
            メンバー: {{ roomStore.room.members.map(m => m.nickname).join(', ') }}
          </p>
        </div>
        <div class="flex items-center gap-2">
          <span
            class="text-xs px-2.5 py-1 rounded-full font-medium"
            :class="{
              'bg-green-800/80 text-green-200 border border-green-700/40': roomStore.room.status === 'active',
              'bg-gray-700 text-gray-400': roomStore.room.status !== 'active',
            }"
          >
            {{ roomStore.room.status === 'active' ? 'アクティブ' : 'クローズ済み' }}
          </span>
          <span
            v-if="pendingClose"
            class="text-xs px-2.5 py-1 rounded-full bg-yellow-800/80 text-yellow-200 border border-yellow-700/40 gm-pulse-glow"
          >
            相手の同意を待っています...
          </span>
          <button
            v-else-if="roomStore.room.status === 'active'"
            @click="handleClose"
            class="px-3 py-1 bg-red-600 hover:bg-red-700 rounded-lg text-sm transition"
          >
            ルームを閉じる
          </button>
          <router-link
            v-if="roomStore.room.status !== 'active'"
            :to="{ name: 'feedback', params: { id: roomId } }"
            class="px-3 py-1 bg-gradient-to-r from-cyan-600 to-indigo-600 hover:from-cyan-500 hover:to-indigo-500 rounded-lg text-sm transition-all"
          >
            フィードバック
          </router-link>
        </div>
      </div>
    </div>

    <!-- Chat -->
    <div
      ref="chatContainer"
      class="bg-gray-800 rounded-xl border border-gray-700/50 h-96 overflow-y-auto p-4 space-y-3 mb-4"
    >
      <div v-if="roomStore.messages.length === 0" class="text-center text-gray-500 py-8 gm-animate-card">
        <div class="text-4xl mb-2">&#x1F4AC;</div>
        まだメッセージがありません
      </div>
      <div
        v-for="msg in roomStore.messages"
        :key="msg.id"
        class="flex flex-col"
        :class="[
          msg.user_id === auth.user?.id ? 'items-end' : 'items-start',
          msg.user_id === auth.user?.id ? 'gm-slide-right' : 'gm-slide-left'
        ]"
      >
        <span class="text-xs text-gray-500 mb-0.5 px-1">{{ msg.nickname }} · {{ formatTime(msg.created_at) }}</span>
        <div
          class="max-w-xs px-3.5 py-2 text-sm"
          :class="msg.user_id === auth.user?.id
            ? 'bg-gradient-to-br from-indigo-600 to-indigo-700 rounded-2xl rounded-br-md'
            : 'bg-gray-700 rounded-2xl rounded-bl-md'"
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
      <div class="flex-1 relative">
        <input
          v-model="newMessage"
          type="text"
          maxlength="500"
          placeholder="メッセージを入力..."
          class="w-full px-4 py-2.5 bg-gray-700 border border-gray-600 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500/30 transition-colors pr-16"
        />
        <span
          v-if="msgCharCount > 0"
          class="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-gray-500"
        >
          {{ msgCharCount }}/500
        </span>
      </div>
      <button
        type="submit"
        :disabled="!newMessage.trim()"
        class="px-6 py-2.5 bg-gradient-to-r from-cyan-600 to-indigo-600 hover:from-cyan-500 hover:to-indigo-500 disabled:opacity-50 disabled:from-gray-600 disabled:to-gray-600 rounded-xl font-medium transition-all"
      >
        送信
      </button>
    </form>
  </div>
  <div v-else class="text-center py-16">
    <div class="gm-spinner-lg mx-auto mb-4"></div>
    <p class="text-gray-500">ルームを読み込み中...</p>
  </div>
</template>
