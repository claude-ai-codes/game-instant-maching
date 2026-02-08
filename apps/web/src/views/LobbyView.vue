<script setup lang="ts">
import { useRecruitmentStore } from '@/stores/recruitment'
import { useAuthStore } from '@/stores/auth'
import { useGameStore } from '@/stores/game'
import { useRoomStore } from '@/stores/room'
import { useRouter } from 'vue-router'
import { onMounted } from 'vue'
import { usePolling } from '@/composables/usePolling'
import { useWebSocket } from '@/composables/useWebSocket'
import { regionName, playStyleName, timeAgo } from '@/utils/data'
import { ref } from 'vue'

const store = useRecruitmentStore()
const auth = useAuthStore()
const gameStore = useGameStore()
const roomStore = useRoomStore()
const router = useRouter()
const joining = ref<string | null>(null)
const error = ref('')

onMounted(() => {
  gameStore.fetchGames()
  roomStore.fetchPendingFeedback()
})

// WebSocket for real-time updates, with slower polling fallback
const { on } = useWebSocket()

on('recruitment_update', () => {
  store.fetchRecruitments()
})

on('match_created', (data) => {
  if (data.room_id) {
    router.push({ name: 'room', params: { id: data.room_id as string } })
  }
})

usePolling(() => store.fetchRecruitments(), 15000)

async function join(id: string) {
  error.value = ''
  joining.value = id
  try {
    const result = await store.joinRecruitment(id)
    router.push({ name: 'room', params: { id: result.room_id } })
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'マッチに失敗しました'
  } finally {
    joining.value = null
  }
}

async function cancel(id: string) {
  await store.cancelRecruitment(id)
}

function formatTime(iso: string) {
  return new Date(iso).toLocaleTimeString('ja-JP', { hour: '2-digit', minute: '2-digit' })
}
</script>

<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-xl font-bold">募集一覧</h1>
      <router-link
        to="/recruit"
        class="px-5 py-2 bg-gradient-to-r from-cyan-600 to-indigo-600 hover:from-cyan-500 hover:to-indigo-500 rounded-lg text-sm font-medium transition-all shadow-lg shadow-indigo-500/20"
      >
        募集を作成
      </router-link>
    </div>

    <div
      v-if="roomStore.pendingFeedbackRoomIds.length > 0"
      class="mb-4 p-3 bg-yellow-900/30 border border-yellow-700 rounded-lg"
    >
      <p class="text-sm text-yellow-300 mb-2">
        &#x1F44D; フィードバック未送信のルームがあります
      </p>
      <div class="flex gap-2 flex-wrap">
        <router-link
          v-for="rid in roomStore.pendingFeedbackRoomIds"
          :key="rid"
          :to="{ name: 'feedback', params: { id: rid } }"
          class="px-3 py-1 bg-yellow-700 hover:bg-yellow-600 rounded text-xs text-white transition"
        >
          フィードバックを送る
        </router-link>
      </div>
    </div>

    <p v-if="error" class="mb-4 text-red-400 text-sm">{{ error }}</p>

    <div v-if="store.recruitments.length === 0" class="text-center py-16 gm-animate-card">
      <div class="text-5xl mb-4">&#x1F3AE;</div>
      <p class="text-gray-400 mb-2">まだ募集がありません</p>
      <p class="text-gray-500 text-sm mb-6">最初の募集を作成して、一緒に遊ぶ仲間を見つけよう</p>
      <router-link
        to="/recruit"
        class="inline-block px-5 py-2 bg-gradient-to-r from-cyan-600 to-indigo-600 hover:from-cyan-500 hover:to-indigo-500 rounded-lg text-sm font-medium transition-all shadow-lg shadow-indigo-500/20"
      >
        募集を作成
      </router-link>
    </div>

    <div class="space-y-3">
      <div
        v-for="(r, index) in store.recruitments"
        :key="r.id"
        class="bg-gray-800 rounded-lg p-4 border border-gray-700/50 gm-card-hover gm-animate-card"
        :style="{ animationDelay: `${index * 0.05}s` }"
      >
        <div class="flex items-start justify-between">
          <div>
            <div class="flex items-center gap-2 mb-1 flex-wrap">
              <span class="font-medium text-cyan-400">{{ gameStore.gameName(r.game) }}</span>
              <span class="text-xs bg-gray-700/80 px-2.5 py-0.5 rounded-full text-gray-300">{{ regionName(r.region) }}</span>
              <span v-if="r.play_style" class="text-xs bg-yellow-900/40 px-2.5 py-0.5 rounded-full text-yellow-300 border border-yellow-700/30">{{ playStyleName(r.play_style) }}</span>
              <span v-if="r.has_microphone" class="text-xs bg-green-900/40 px-2.5 py-0.5 rounded-full text-green-300 border border-green-700/30">MIC</span>
            </div>
            <div class="text-sm text-gray-400">
              <span>{{ r.nickname }}</span>
              <span v-if="r.thumbs_up_count > 0" class="ml-1 text-yellow-400">&#x1F44D;{{ r.thumbs_up_count }}</span>
              <span class="mx-2">·</span>
              <span>開始: {{ formatTime(r.start_time) }}</span>
              <span v-if="r.desired_role" class="mx-2">·</span>
              <span v-if="r.desired_role">{{ r.desired_role }}</span>
              <span class="mx-2">·</span>
              <span class="text-gray-500">{{ timeAgo(r.created_at) }}</span>
            </div>
            <p v-if="r.memo" class="text-sm text-gray-500 mt-1">{{ r.memo }}</p>
          </div>
          <div class="flex-shrink-0 ml-4">
            <button
              v-if="r.user_id !== auth.user?.id"
              @click="join(r.id)"
              :disabled="joining === r.id"
              class="px-4 py-1.5 bg-green-600 hover:bg-green-700 disabled:opacity-50 rounded-lg text-sm font-medium transition shadow-sm flex items-center gap-1.5"
            >
              <span v-if="joining === r.id" class="gm-spinner" style="width:0.85em;height:0.85em;"></span>
              {{ joining === r.id ? '参加中...' : '参加する' }}
            </button>
            <button
              v-else
              @click="cancel(r.id)"
              class="px-4 py-1.5 bg-red-600 hover:bg-red-700 rounded-lg text-sm font-medium transition"
            >
              取り消し
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
