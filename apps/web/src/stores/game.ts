import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api } from '@/composables/useApi'

interface GameItem {
  id: string
  slug: string
  name: string
  name_ja: string | null
  category: string
  platform_tags: string[] | null
}

export const useGameStore = defineStore('game', () => {
  const games = ref<GameItem[]>([])
  const loaded = ref(false)

  async function fetchGames() {
    if (loaded.value) return
    games.value = await api<GameItem[]>('/api/games')
    loaded.value = true
  }

  const categories = computed(() => {
    const cats = new Set(games.value.map(g => g.category))
    return Array.from(cats).sort()
  })

  function gameName(slug: string): string {
    const g = games.value.find(g => g.slug === slug)
    return g?.name_ja ?? g?.name ?? slug
  }

  return { games, loaded, fetchGames, categories, gameName }
})
