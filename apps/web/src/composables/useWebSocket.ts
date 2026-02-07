import { ref, onUnmounted } from 'vue'
import { api } from '@/composables/useApi'

type Handler = (data: Record<string, unknown>) => void

export function useWebSocket() {
  const connected = ref(false)
  let ws: WebSocket | null = null
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null
  let pingTimer: ReturnType<typeof setInterval> | null = null
  let backoff = 1000
  let destroyed = false

  const handlers = new Map<string, Set<Handler>>()

  function on(event: string, handler: Handler) {
    if (!handlers.has(event)) {
      handlers.set(event, new Set())
    }
    handlers.get(event)!.add(handler)
  }

  function off(event: string, handler: Handler) {
    handlers.get(event)?.delete(handler)
  }

  function dispatch(type: string, data: Record<string, unknown>) {
    const set = handlers.get(type)
    if (set) {
      for (const h of set) {
        try { h(data) } catch { /* handler error */ }
      }
    }
  }

  async function connect() {
    if (destroyed) return
    try {
      const { ticket } = await api<{ ticket: string }>('/api/ws/ticket', { method: 'POST' })
      const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:'
      ws = new WebSocket(`${protocol}//${location.host}/api/ws?ticket=${ticket}`)

      ws.onopen = () => {
        connected.value = true
        backoff = 1000
        startPing()
      }

      ws.onmessage = (event) => {
        if (event.data === 'pong') return
        try {
          const msg = JSON.parse(event.data)
          if (msg.type) {
            dispatch(msg.type, msg.data || {})
          }
        } catch { /* ignore malformed messages */ }
      }

      ws.onclose = () => {
        connected.value = false
        stopPing()
        scheduleReconnect()
      }

      ws.onerror = () => {
        ws?.close()
      }
    } catch {
      scheduleReconnect()
    }
  }

  function scheduleReconnect() {
    if (destroyed) return
    reconnectTimer = setTimeout(() => {
      backoff = Math.min(backoff * 2, 30000)
      connect()
    }, backoff)
  }

  function startPing() {
    stopPing()
    pingTimer = setInterval(() => {
      if (ws?.readyState === WebSocket.OPEN) {
        ws.send('ping')
      }
    }, 30000)
  }

  function stopPing() {
    if (pingTimer) {
      clearInterval(pingTimer)
      pingTimer = null
    }
  }

  function disconnect() {
    destroyed = true
    if (reconnectTimer) clearTimeout(reconnectTimer)
    stopPing()
    if (ws) {
      ws.onclose = null
      ws.close()
      ws = null
    }
    connected.value = false
  }

  // Auto-connect on creation
  connect()

  onUnmounted(() => {
    disconnect()
  })

  return { connected, on, off, disconnect }
}
