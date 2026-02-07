import { onMounted, onUnmounted, ref } from 'vue'

export function usePolling(fn: () => Promise<void>, intervalMs: number = 3000) {
  const timer = ref<ReturnType<typeof setInterval> | null>(null)

  const safeFn = async () => {
    try {
      await fn()
    } catch {
      // Silently ignore polling errors to keep the interval alive
    }
  }

  onMounted(() => {
    safeFn()
    timer.value = setInterval(safeFn, intervalMs)
  })

  onUnmounted(() => {
    if (timer.value) {
      clearInterval(timer.value)
    }
  })

  return { timer }
}
