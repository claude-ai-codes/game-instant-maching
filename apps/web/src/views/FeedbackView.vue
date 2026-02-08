<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useRoomStore } from '@/stores/room'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const roomStore = useRoomStore()
const auth = useAuthStore()
const roomId = route.params.id as string
const submitted = ref(false)
const error = ref('')

const otherMember = computed(() => {
  return roomStore.room?.members.find(m => m.user_id !== auth.user?.id)
})

onMounted(async () => {
  if (!roomStore.room || roomStore.room.id !== roomId) {
    await roomStore.fetchRoom(roomId)
  }
})

async function giveFeedback(rating: 'thumbs_up' | 'thumbs_down') {
  if (!otherMember.value) return
  error.value = ''
  try {
    await roomStore.submitFeedback(roomId, otherMember.value.user_id, rating)
    submitted.value = true
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'フィードバック送信に失敗しました'
  }
}
</script>

<template>
  <div class="max-w-md mx-auto text-center">
    <h1 class="text-xl font-bold mb-6">フィードバック</h1>

    <div v-if="!submitted" class="gm-animate-card">
      <p class="text-gray-400 mb-6">
        <span v-if="otherMember">{{ otherMember.nickname }}</span> さんとの対戦はいかがでしたか？
      </p>
      <div class="flex justify-center gap-6 mb-6">
        <button
          @click="giveFeedback('thumbs_up')"
          class="flex flex-col items-center gap-2 px-10 py-6 bg-gray-800 hover:bg-green-900/60 border border-gray-700 hover:border-green-500 rounded-xl transition-all hover:-translate-y-0.5 hover:shadow-lg hover:shadow-green-900/20 group"
        >
          <span class="text-5xl transition-transform group-hover:scale-110">&#x1F44D;</span>
          <span class="text-sm text-gray-400">良かった</span>
        </button>
        <button
          @click="giveFeedback('thumbs_down')"
          class="flex flex-col items-center gap-2 px-10 py-6 bg-gray-800 hover:bg-red-900/60 border border-gray-700 hover:border-red-500 rounded-xl transition-all hover:-translate-y-0.5 hover:shadow-lg hover:shadow-red-900/20 group"
        >
          <span class="text-5xl transition-transform group-hover:scale-110">&#x1F44E;</span>
          <span class="text-sm text-gray-400">微妙だった</span>
        </button>
      </div>
      <p v-if="error" class="text-red-400 text-sm mb-4">{{ error }}</p>
      <router-link to="/lobby" class="text-sm text-gray-500 hover:text-gray-300 transition-colors">
        スキップしてロビーに戻る
      </router-link>
    </div>

    <div v-else class="gm-animate-scale">
      <div class="gm-animate-check inline-block mb-4">
        <span class="text-5xl">&#x2705;</span>
      </div>
      <p class="text-green-400 mb-6">フィードバックを送信しました。ありがとう！</p>
      <router-link
        to="/lobby"
        class="px-6 py-2.5 bg-gradient-to-r from-cyan-600 to-indigo-600 hover:from-cyan-500 hover:to-indigo-500 rounded-lg font-medium transition-all shadow-lg shadow-indigo-500/20 inline-block"
      >
        ロビーに戻る
      </router-link>
    </div>
  </div>
</template>
