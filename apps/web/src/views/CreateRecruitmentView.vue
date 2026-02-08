<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useRecruitmentStore } from '@/stores/recruitment'
import { useGameStore } from '@/stores/game'
import { REGIONS, PLAY_STYLES } from '@/utils/data'
import type { PlayStyle } from '@/types'

const store = useRecruitmentStore()
const gameStore = useGameStore()
const router = useRouter()

onMounted(() => gameStore.fetchGames())

const game = ref('valorant')
const region = ref('jp')
const futureDate = new Date(Date.now() + 15 * 60 * 1000)
const startTime = ref(
  `${futureDate.getFullYear()}-${String(futureDate.getMonth() + 1).padStart(2, '0')}-${String(futureDate.getDate()).padStart(2, '0')}T${String(futureDate.getHours()).padStart(2, '0')}:${String(futureDate.getMinutes()).padStart(2, '0')}`
)
const desiredRole = ref('')
const memo = ref('')
const playStyle = ref<PlayStyle | ''>('')
const hasMicrophone = ref(false)
const error = ref('')

const memoCount = computed(() => memo.value.length)

async function handleCreate() {
  error.value = ''
  if (new Date(startTime.value) < new Date()) {
    error.value = '開始時刻は現在より後を指定してください'
    return
  }
  try {
    await store.createRecruitment({
      game: game.value,
      region: region.value,
      start_time: new Date(startTime.value).toISOString(),
      desired_role: desiredRole.value || undefined,
      memo: memo.value || undefined,
      play_style: playStyle.value || undefined,
      has_microphone: hasMicrophone.value,
    })
    router.push({ name: 'lobby' })
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : '募集の作成に失敗しました'
  }
}
</script>

<template>
  <div class="max-w-md mx-auto">
    <h1 class="text-xl font-bold mb-6">募集を作成</h1>
    <form @submit.prevent="handleCreate" class="space-y-6">
      <!-- Required section -->
      <div class="bg-gray-800/50 rounded-xl p-5 space-y-4 border border-gray-700/30">
        <div>
          <label class="block text-sm text-gray-400 mb-1">ゲーム</label>
          <select v-model="game" class="w-full px-3 py-2.5 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500/30 transition-colors">
            <option v-for="g in gameStore.games" :key="g.slug" :value="g.slug">{{ g.name_ja ?? g.name }}</option>
          </select>
        </div>
        <div>
          <label class="block text-sm text-gray-400 mb-1">地域/サーバー</label>
          <select v-model="region" class="w-full px-3 py-2.5 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500/30 transition-colors">
            <option v-for="r in REGIONS" :key="r.id" :value="r.id">{{ r.name }}</option>
          </select>
        </div>
        <div>
          <label class="block text-sm text-gray-400 mb-1">開始可能時刻</label>
          <input
            v-model="startTime"
            type="datetime-local"
            class="w-full px-3 py-2.5 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500/30 transition-colors"
          />
        </div>
      </div>

      <!-- Optional section -->
      <div class="bg-gray-800/30 rounded-xl p-5 space-y-4 border border-gray-700/20">
        <p class="text-xs text-gray-500 -mt-1 mb-1">オプション</p>
        <div>
          <label class="block text-sm text-gray-400 mb-1">希望ロール（任意）</label>
          <input
            v-model="desiredRole"
            type="text"
            maxlength="50"
            placeholder="例: サポート"
            class="w-full px-3 py-2.5 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500/30 transition-colors"
          />
        </div>
        <div>
          <label class="block text-sm text-gray-400 mb-1">プレイスタイル（任意）</label>
          <select v-model="playStyle" class="w-full px-3 py-2.5 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500/30 transition-colors">
            <option value="">未指定</option>
            <option v-for="ps in PLAY_STYLES" :key="ps.id" :value="ps.id">{{ ps.name }}</option>
          </select>
        </div>
        <div class="flex items-center gap-2">
          <input
            v-model="hasMicrophone"
            type="checkbox"
            id="hasMicrophone"
            class="w-4 h-4 rounded bg-gray-700 border-gray-600 text-cyan-500 focus:ring-cyan-500"
          />
          <label for="hasMicrophone" class="text-sm text-gray-400">マイクあり</label>
        </div>
        <div>
          <div class="flex justify-between items-center mb-1">
            <label class="block text-sm text-gray-400">メモ（任意）</label>
            <span v-if="memoCount > 0" class="text-xs text-gray-500">{{ memoCount }}/200</span>
          </div>
          <textarea
            v-model="memo"
            maxlength="200"
            rows="2"
            placeholder="カジュアルに楽しみたいです"
            class="w-full px-3 py-2.5 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-500 resize-none focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500/30 transition-colors"
          />
        </div>
      </div>

      <p v-if="error" class="text-red-400 text-sm">{{ error }}</p>

      <div class="flex gap-3">
        <button
          type="submit"
          :disabled="store.loading"
          class="flex-1 py-2.5 bg-gradient-to-r from-cyan-600 to-indigo-600 hover:from-cyan-500 hover:to-indigo-500 disabled:opacity-50 rounded-lg font-medium transition-all shadow-lg shadow-indigo-500/20 flex items-center justify-center gap-2"
        >
          <span v-if="store.loading" class="gm-spinner"></span>
          {{ store.loading ? '作成中...' : '募集する' }}
        </button>
        <router-link
          to="/lobby"
          class="flex-1 py-2.5 bg-gray-700 hover:bg-gray-600 rounded-lg font-medium text-center transition"
        >
          キャンセル
        </router-link>
      </div>
    </form>
  </div>
</template>
