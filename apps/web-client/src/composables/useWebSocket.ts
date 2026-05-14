import { ref, onUnmounted } from 'vue'
import { createWsClient, type WsClientOptions } from '../websocket'

export function useWebSocket(options: Omit<WsClientOptions, 'refreshToken'>) {
  const isConnected = ref(false)
  const messages = ref<any[]>([])

  // 复用 api/index.js 的 token 刷新逻辑
  const refreshToken = async () => {
    const refresh_token = localStorage.getItem('refresh_token')
    if (!refresh_token) throw new Error('No refresh token')

    const response = await fetch(`${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/api/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token })
    })

    if (!response.ok) throw new Error('Refresh failed')

    const { access_token, refresh_token: newRefresh } = await response.json()
    localStorage.setItem('access_token', access_token)
    localStorage.setItem('refresh_token', newRefresh)
    return { access_token, refresh_token: newRefresh }
  }

  const client = createWsClient({
    ...options,
    refreshToken,
    onMessage: (data) => {
      messages.value.push(data)
      options.onMessage(data)
    }
  })

  const connect = () => {
    const token = localStorage.getItem('access_token')
    if (token) {
      client.connect(token)
      isConnected.value = true
    }
  }

  const disconnect = () => {
    client.disconnect()
    isConnected.value = false
  }

  onUnmounted(() => {
    disconnect()
  })

  return {
    isConnected,
    messages,
    connect,
    disconnect
  }
}
