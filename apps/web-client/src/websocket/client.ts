export interface WsClientOptions {
  onMessage: (data: any) => void
  onClose?: (code: number) => void
  onError?: (error: Event) => void
  refreshToken: () => Promise<{ access_token: string; refresh_token: string }>
}

interface WsClient {
  connect(token: string): void
  disconnect(): void
  send(data: object): void
}

const CLOSE_CODE_TOKEN_ERROR = 4001

export function createWsClient(options: WsClientOptions): WsClient {
  const { onMessage, onClose, onError, refreshToken } = options

  let ws: WebSocket | null = null
  let token = ''
  let retryCount = 0
  let retryTimer: number | null = null
  let destroyed = false
  let heartbeatTimer: number | null = null

  // 重试延迟：3s -> 6s -> 12s -> 24s -> 30s（最多10次）
  const RETRY_DELAYS = [3000, 6000, 12000, 24000, 30000, 30000, 30000, 30000, 30000, 30000]
  const MAX_RETRIES = 10
  const HEARTBEAT_INTERVAL = 30000 // 30秒

  function getWsUrl() {
    const base = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
    return base.replace('http', 'ws')
  }

  function startHeartbeat() {
    stopHeartbeat()
    heartbeatTimer = window.setInterval(() => {
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'ping' }))
      }
    }, HEARTBEAT_INTERVAL)
  }

  function stopHeartbeat() {
    if (heartbeatTimer) {
      clearInterval(heartbeatTimer)
      heartbeatTimer = null
    }
  }

  function connect(newToken: string) {
    if (retryTimer) {
      clearTimeout(retryTimer)
      retryTimer = null
    }
    token = newToken
    destroyed = false
    retryCount = 0

    ws = new WebSocket(`${getWsUrl()}/api/ws?token=${token}`)

    ws.onopen = () => {
      startHeartbeat()
    }

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        if (data.type === 'dynamic') {
          onMessage(data)
        }
      } catch (e) {
        // ignore parse error
      }
    }

    ws.onclose = (event) => {
      stopHeartbeat()

      if (destroyed) return

      if (event.code === CLOSE_CODE_TOKEN_ERROR) {
        // token 错误，立即刷新，不消耗重试次数
        refreshToken()
          .then(({ access_token }) => {
            connect(access_token)
          })
          .catch(() => {
            destroyed = true
            onClose?.(event.code)
          })
        return
      }

      // 普通断线，重试
      if (retryCount < MAX_RETRIES) {
        const delay = RETRY_DELAYS[retryCount] || 30000
        retryCount++
        retryTimer = window.setTimeout(() => connect(token), delay)
      } else {
        onClose?.(event.code)
      }
    }

    ws.onerror = (error) => {
      onError?.(error)
    }
  }

  function disconnect() {
    destroyed = true
    stopHeartbeat()
    if (retryTimer) {
      clearTimeout(retryTimer)
      retryTimer = null
    }
    if (ws) {
      ws.close()
      ws = null
    }
  }

  function send(data: object) {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(data))
    }
  }

  return { connect, disconnect, send }
}
