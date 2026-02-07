import { onMounted, onUnmounted, ref } from 'vue'

export function usePolling(fn: () => Promise<void>, intervalMs: number = 3000) {
  const timer = ref<ReturnType<typeof setInterval> | null>(null)

  onMounted(() => {
    fn()
    timer.value = setInterval(fn, intervalMs)
  })

  onUnmounted(() => {
    if (timer.value) {
      clearInterval(timer.value)
    }
  })

  return { timer }
}
