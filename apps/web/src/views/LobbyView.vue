<script setup lang="ts">
import { useRecruitmentStore } from '@/stores/recruitment'
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'
import { usePolling } from '@/composables/usePolling'
import { useWebSocket } from '@/composables/useWebSocket'
import { gameName, regionName } from '@/utils/data'
import { ref } from 'vue'

const store = useRecruitmentStore()
const auth = useAuthStore()
const router = useRouter()
const joining = ref<string | null>(null)
const error = ref('')

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
        class="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm font-medium transition"
      >
        募集を作成
      </router-link>
    </div>

    <p v-if="error" class="mb-4 text-red-400 text-sm">{{ error }}</p>

    <div v-if="store.recruitments.length === 0" class="text-center text-gray-500 py-12">
      まだ募集がありません。最初の募集を作成しましょう！
    </div>

    <div class="space-y-3">
      <div
        v-for="r in store.recruitments"
        :key="r.id"
        class="bg-gray-800 rounded-lg p-4 border border-gray-700"
      >
        <div class="flex items-start justify-between">
          <div>
            <div class="flex items-center gap-2 mb-1">
              <span class="font-medium text-blue-400">{{ gameName(r.game) }}</span>
              <span class="text-xs bg-gray-700 px-2 py-0.5 rounded text-gray-300">{{ regionName(r.region) }}</span>
            </div>
            <div class="text-sm text-gray-400">
              <span>{{ r.nickname }}</span>
              <span class="mx-2">·</span>
              <span>開始: {{ formatTime(r.start_time) }}</span>
              <span v-if="r.desired_role" class="mx-2">·</span>
              <span v-if="r.desired_role">{{ r.desired_role }}</span>
            </div>
            <p v-if="r.memo" class="text-sm text-gray-500 mt-1">{{ r.memo }}</p>
          </div>
          <div class="flex-shrink-0 ml-4">
            <button
              v-if="r.user_id !== auth.user?.id"
              @click="join(r.id)"
              :disabled="joining === r.id"
              class="px-4 py-1.5 bg-green-600 hover:bg-green-700 disabled:opacity-50 rounded text-sm font-medium transition"
            >
              {{ joining === r.id ? '参加中...' : '参加する' }}
            </button>
            <button
              v-else
              @click="cancel(r.id)"
              class="px-4 py-1.5 bg-red-600 hover:bg-red-700 rounded text-sm font-medium transition"
            >
              取り消し
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
