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

    <div v-if="!submitted">
      <p class="text-gray-400 mb-6">
        <span v-if="otherMember">{{ otherMember.nickname }}</span> さんとの対戦はいかがでしたか？
      </p>
      <div class="flex justify-center gap-6 mb-6">
        <button
          @click="giveFeedback('thumbs_up')"
          class="flex flex-col items-center gap-2 px-8 py-4 bg-gray-800 hover:bg-green-900 border border-gray-700 hover:border-green-500 rounded-lg transition"
        >
          <span class="text-4xl">&#x1F44D;</span>
          <span class="text-sm text-gray-400">良かった</span>
        </button>
        <button
          @click="giveFeedback('thumbs_down')"
          class="flex flex-col items-center gap-2 px-8 py-4 bg-gray-800 hover:bg-red-900 border border-gray-700 hover:border-red-500 rounded-lg transition"
        >
          <span class="text-4xl">&#x1F44E;</span>
          <span class="text-sm text-gray-400">微妙だった</span>
        </button>
      </div>
      <p v-if="error" class="text-red-400 text-sm mb-4">{{ error }}</p>
      <router-link to="/lobby" class="text-sm text-gray-500 hover:text-gray-300">
        スキップしてロビーに戻る
      </router-link>
    </div>

    <div v-else>
      <p class="text-green-400 mb-6">フィードバックを送信しました。ありがとう！</p>
      <router-link
        to="/lobby"
        class="px-6 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg font-medium transition inline-block"
      >
        ロビーに戻る
      </router-link>
    </div>
  </div>
</template>
