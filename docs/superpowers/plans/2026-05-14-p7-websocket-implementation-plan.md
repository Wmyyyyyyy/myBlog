# P7 WebSocket 实时推送实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现 WebSocket 实时推送用户动态流事件，支持多设备同时在线，并提供 Admin 后台在线用户统计。

**Architecture:**
- FastAPI 原生 WebSocket + Redis Pub/Sub
- 连接管理器维护 `Dict[user_id, List[WebSocket]]` 支持多设备
- 后台 asyncio 任务每 30s 清理超时连接
- 动态事件通过 Redis Channel 广播，各 worker 推送给在线粉丝

**Tech Stack:** FastAPI WebSocket, Redis Pub/Sub, asyncio, TypeScript, Vue Composables

---

## 文件结构

```
backend/apps/
├── websocket/
│   ├── __init__.py
│   ├── manager.py       # ConnectionManager（多设备支持）
│   ├── router.py        # WebSocket 路由 + JWT 认证
│   ├── consumer.py      # Redis Pub/Sub 消费者
│   └── tasks.py         # 后台清理任务
├── interactions/
│   └── services.py      # 修改：发布 Redis 消息
└── blogs/
    └── services.py      # 修改：发布 Redis 消息

backend/main.py           # 注册 websocket 路由

web-client/src/
├── websocket/
│   ├── client.ts        # WsClient 实现
│   └── index.ts
└── composables/
    └── useWebSocket.ts  # Vue composable
```

---

## Task 1: ConnectionManager（多设备支持）

**Files:**
- Create: `backend/apps/websocket/manager.py`
- Test: `tests/apps/websocket/test_manager.py`

- [ ] **Step 1: Write失败测试**

```python
# tests/apps/websocket/test_manager.py
import pytest
from apps.websocket.manager import ConnectionManager

@pytest.fixture
def manager():
    return ConnectionManager()

def test_single_connection(manager):
    """单设备连接测试"""
    user_id = 1
    # Mock WebSocket
    class MockWS:
        pass
    ws = MockWS()

    # connect 应该成功
    assert len(manager.connections.get(user_id, [])) == 0

    # 注册连接
    manager.connections.setdefault(user_id, []).append(ws)

    # 应该有一个连接
    assert len(manager.connections[user_id]) == 1

def test_multi_device(manager):
    """多设备同时在线"""
    user_id = 1
    ws1, ws2 = MockWS(), MockWS()

    manager.connections.setdefault(user_id, []).append(ws1)
    manager.connections.setdefault(user_id, []).append(ws2)

    # 同一用户两个连接
    assert len(manager.connections[user_id]) == 2

def test_disconnect_one_device(manager):
    """断开一个设备，另一个保持"""
    user_id = 1
    ws1, ws2 = MockWS(), MockWS()

    manager.connections.setdefault(user_id, []).append(ws1)
    manager.connections.setdefault(user_id, []).append(ws2)

    manager.connections[user_id].remove(ws1)

    assert len(manager.connections[user_id]) == 1
    assert ws1 not in manager.connections[user_id]
    assert ws2 in manager.connections[user_id]

def test_last_user_disconnect_removes_key(manager):
    """最后一个连接断开时移除 key"""
    user_id = 1
    ws = MockWS()

    manager.connections.setdefault(user_id, []).append(ws)

    manager.connections[user_id].remove(ws)
    if not manager.connections[user_id]:
        del manager.connections[user_id]

    assert user_id not in manager.connections
```

- [ ] **Step 2: 运行测试验证失败**

Run: `cd e:/code/myBlog/backend && python -m pytest tests/apps/websocket/test_manager.py -v`
Expected: FAIL - module not found

- [ ] **Step 3: 创建目录结构**

```bash
mkdir -p e:/code/myBlog/backend/apps/websocket
touch e:/code/myBlog/backend/apps/websocket/__init__.py
mkdir -p e:/code/myBlog/backend/tests/apps/websocket
touch e:/code/myBlog/backend/tests/apps/websocket/__init__.py
```

- [ ] **Step 4: 实现 ConnectionManager**

```python
# backend/apps/websocket/manager.py
import time
from typing import Dict, List
from fastapi import WebSocket
import redis.asyncio as redis
from core.config import settings

class ConnectionManager:
    def __init__(self):
        # user_id -> [WebSocket, ...]（支持多设备）
        self.connections: Dict[int, List[WebSocket]] = {}
        # WebSocket -> 最后活跃时间
        self.last_heartbeat: Dict[WebSocket, float] = {}
        self._redis: redis.Redis = None

    async def _get_redis(self) -> redis.Redis:
        if self._redis is None:
            self._redis = redis.from_url(settings.REDIS_URL)
        return self._redis

    async def connect(self, ws: WebSocket, user_id: int):
        """注册连接"""
        await ws.accept()
        self.connections.setdefault(user_id, []).append(ws)
        self.last_heartbeat[ws] = time.time()
        # 设置 Redis 在线状态
        r = await self._get_redis()
        await r.setex(f"ws:online:{user_id}", 60, "1")

    async def disconnect(self, ws: WebSocket, user_id: int):
        """断开连接"""
        if user_id in self.connections:
            if ws in self.connections[user_id]:
                self.connections[user_id].remove(ws)
            if not self.connections[user_id]:
                del self.connections[user_id]
                r = await self._get_redis()
                await r.delete(f"ws:online:{user_id}")
        self.last_heartbeat.pop(ws, None)

    async def heartbeat(self, ws: WebSocket, user_id: int):
        """心跳刷新"""
        self.last_heartbeat[ws] = time.time()
        r = await self._get_redis()
        await r.setex(f"ws:online:{user_id}", 60, "1")

    async def broadcast_to_users(self, user_ids: List[int], message: dict):
        """向指定用户的所有连接推送消息"""
        for user_id in user_ids:
            if user_id in self.connections:
                dead_ws = []
                for ws in self.connections[user_id]:
                    try:
                        await ws.send_json(message)
                    except Exception:
                        dead_ws.append(ws)
                # 清理死连接
                for ws in dead_ws:
                    await self.disconnect(ws, user_id)

    async def purge_inactive(self, timeout: float = 60.0):
        """清理超时连接（后台任务调用）"""
        now = time.time()
        dead_connections = []

        for ws, last_time in list(self.last_heartbeat.items()):
            if now - last_time > timeout:
                dead_connections.append(ws)

        for ws in dead_connections:
            # 找到对应的 user_id
            for user_id, ws_list in list(self.connections.items()):
                if ws in ws_list:
                    await self.disconnect(ws, user_id)
                    break

    async def get_online_count(self) -> int:
        """获取在线用户数（Admin 用）"""
        r = await self._get_redis()
        count = 0
        cursor = 0
        while True:
            cursor, keys = await r.scan(cursor=cursor, match="ws:online:*", count=100)
            count += len(keys)
            if cursor == 0:
                break
        return count


# 全局单例
manager = ConnectionManager()
```

- [ ] **Step 5: 运行测试验证通过**

Run: `cd e:/code/myBlog/backend && python -m pytest tests/apps/websocket/test_manager.py -v`
Expected: PASS

- [ ] **Step 6: 提交**

```bash
cd e:/code/myBlog
git add backend/apps/websocket/manager.py tests/apps/websocket/test_manager.py
git commit -m "feat(P7): add ConnectionManager with multi-device support"
```

---

## Task 2: WebSocket 路由 + JWT 认证

**Files:**
- Create: `backend/apps/websocket/router.py`
- Modify: `backend/main.py`（注册路由）

- [ ] **Step 1: 写失败测试**

```python
# tests/apps/websocket/test_router.py
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock

# 测试需要验证：
# 1. 无 token 返回 403
# 2. 无效 token 返回 403
# 3. 有效 token 建立连接
# 4. 收到 ping 返回 pong
```

Run: `cd e:/code/myBlog/backend && python -m pytest tests/apps/websocket/test_router.py -v`
Expected: FAIL - module not found

- [ ] **Step 2: 实现 WebSocket 路由**

```python
# backend/apps/websocket/router.py
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, HTTPException
from core.security import decode_token
from core.redis import redis_client
from apps.websocket.manager import manager

router = APIRouter()

# 关闭码
CLOSE_CODE_TOKEN_ERROR = 4001
CLOSE_CODE_BANNED = 4002
CLOSE_CODE_SERVER_ERROR = 4003


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(..., description="JWT access token")
):
    """WebSocket 连接入口"""
    # 1. 验证 token
    payload = decode_token(token)
    if payload is None:
        await websocket.close(code=CLOSE_CODE_TOKEN_ERROR)
        return

    user_id = payload.get("sub")
    if not user_id:
        await websocket.close(code=CLOSE_CODE_TOKEN_ERROR)
        return

    # 2. 注册连接
    await manager.connect(websocket, int(user_id))

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            if message.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
                await manager.heartbeat(websocket, int(user_id))
            else:
                # 忽略未知消息类型
                pass

    except WebSocketDisconnect:
        await manager.disconnect(websocket, int(user_id))
    except Exception:
        await manager.disconnect(websocket, int(user_id))
```

- [ ] **Step 3: 注册路由到 main.py**

```python
# backend/main.py 修改
from apps.websocket.router import router as websocket_router

# 在 app = FastAPI(...) 后添加
app.include_router(websocket_router, prefix="/api")
```

- [ ] **Step 4: 提交**

```bash
git add backend/apps/websocket/router.py backend/main.py
git commit -m "feat(P7): add WebSocket router with JWT auth"
```

---

## Task 3: Redis Pub/Sub 消费者

**Files:**
- Create: `backend/apps/websocket/consumer.py`
- Modify: `backend/main.py`（启动时初始化消费者）

- [ ] **Step 1: 实现 Redis Pub/Sub 消费者**

```python
# backend/apps/websocket/consumer.py
import json
import asyncio
from typing import Optional
import redis.asyncio as redis
from core.config import settings
from apps.websocket.manager import manager

CHANNEL = "dynamic_events"


class PubSubConsumer:
    def __init__(self):
        self._redis: Optional[redis.Redis] = None
        self._pubsub: Optional[redis.client.PubSub] = None
        self._task: Optional[asyncio.Task] = None

    async def _get_redis(self) -> redis.Redis:
        if self._redis is None:
            self._redis = redis.from_url(settings.REDIS_URL)
        return self._redis

    async def start(self):
        """启动消费者（主进程调用）"""
        self._task = asyncio.create_task(self._consume())

    async def stop(self):
        """停止消费者"""
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def _consume(self):
        """消费 Redis 消息"""
        r = await self._get_redis()
        self._pubsub = r.pubsub()
        await self._pubsub.subscribe(CHANNEL)

        try:
            async for message in self._pubsub.listen():
                if message["type"] == "message":
                    await self._handle_message(message["data"])
        except asyncio.CancelledError:
            pass
        finally:
            await self._pubsub.unsubscribe(CHANNEL)
            await self._pubsub.close()

    async def _handle_message(self, data: bytes):
        """处理动态事件消息"""
        try:
            msg = json.loads(data.decode())
        except Exception:
            return

        if msg.get("type") != "dynamic":
            return

        event_type = msg.get("event_type")
        user_id = msg.get("user_id")
        target_user_ids = msg.get("target_user_ids", [])

        if not target_user_ids:
            return

        # 推送消息给目标用户
        push_message = {
            "type": "dynamic",
            "event_type": event_type,
            "user_id": user_id,
            "data": msg.get("data", {})
        }

        await manager.broadcast_to_users(target_user_ids, push_message)


# 全局单例
consumer = PubSubConsumer()
```

- [ ] **Step 2: 修改 main.py 启动/关闭消费者**

```python
# backend/main.py 修改
from contextlib import asynccontextmanager
from apps.websocket.consumer import consumer

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时
    await consumer.start()
    yield
    # 关闭时
    await consumer.stop()
    await close_redis()
```

- [ ] **Step 3: 提交**

```bash
git add backend/apps/websocket/consumer.py backend/main.py
git commit -m "feat(P7): add Redis Pub/Sub consumer for dynamic events"
```

---

## Task 4: 后台清理任务

**Files:**
- Create: `backend/apps/websocket/tasks.py`
- Modify: `backend/main.py`（注册后台任务）

- [ ] **Step 1: 实现后台清理任务**

```python
# backend/apps/websocket/tasks.py
import asyncio
from apps.websocket.manager import manager

PURGE_INTERVAL = 30  # 秒
PURGE_TIMEOUT = 60   # 超时秒数


async def _purge_loop():
    """定期清理超时连接的后台任务"""
    while True:
        try:
            await asyncio.sleep(PURGE_INTERVAL)
            await manager.purge_inactive(timeout=PURGE_TIMEOUT)
        except asyncio.CancelledError:
            break
        except Exception:
            # 记录错误但不中断
            pass


_purge_task: asyncio.Task = None


def start_purge_task():
    global _purge_task
    _purge_task = asyncio.create_task(_purge_loop())


def stop_purge_task():
    global _purge_task
    if _purge_task:
        _purge_task.cancel()
```

- [ ] **Step 2: 修改 main.py 启动/关闭**

```python
# backend/main.py 修改
from apps.websocket.tasks import start_purge_task, stop_purge_task

@asynccontextmanager
async def lifespan(app: FastAPI):
    await consumer.start()
    start_purge_task()
    yield
    stop_purge_task()
    await consumer.stop()
    await close_redis()
```

- [ ] **Step 3: 提交**

```bash
git add backend/apps/websocket/tasks.py backend/main.py
git commit -m "feat(P7): add background task to purge inactive connections"
```

---

## Task 5: 发布动态事件到 Redis

**Files:**
- Modify: `backend/apps/interactions/services.py`
- Modify: `backend/apps/blogs/services.py`

- [ ] **Step 1: 添加 Redis 发布逻辑到 InteractionService**

```python
# backend/apps/interactions/services.py
# 在 add_like 方法末尾添加：
async def add_like(self, user_id: str, blog_id: str):
    # ... 现有逻辑 ...

    # 发布动态事件
    await self._publish_dynamic_event(
        event_type="like_blog",
        user_id=user_id,
        target_id=blog_id,
        data={"blog_id": blog_id}
    )

async def _publish_dynamic_event(self, event_type: str, user_id: str, target_id: str, data: dict):
    """发布动态事件到 Redis"""
    # 查粉丝列表
    followers = await self.get_followers(user_id, skip=0, limit=1000)
    follower_ids = [f.follower_id for f in followers]

    if not follower_ids:
        return

    message = {
        "type": "dynamic",
        "event_type": event_type,
        "user_id": user_id,
        "target_id": target_id,
        "data": data,
        "target_user_ids": follower_ids
    }

    import redis.asyncio as redis
    from core.config import settings
    r = redis.from_url(settings.REDIS_URL)
    await r.publish("dynamic_events", json.dumps(message, default=str))
    await r.close()
```

- [ ] **Step 2: 添加 Redis 发布逻辑到 BlogService**

```python
# backend/apps/blogs/services.py
# 在 create_blog 方法末尾添加发布逻辑（类似上面）
```

- [ ] **Step 3: 提交**

```bash
git add backend/apps/interactions/services.py backend/apps/blogs/services.py
git commit -m "feat(P7): publish dynamic events to Redis on like/follow/blog"
```

---

## Task 6: Admin 在线用户 API

**Files:**
- Create: `backend/apps/admin/views.py` 或修改现有

- [ ] **Step 1: 添加在线用户接口**

```python
# backend/apps/admin/views.py 添加
@router.get("/dashboard/online-users")
async def get_online_users():
    from apps.websocket.manager import manager
    count = await manager.get_online_count()
    return {"online_count": count}
```

- [ ] **Step 2: 提交**

```bash
git add backend/apps/admin/views.py
git commit -m "feat(P7): add admin API for online users count"
```

---

## Task 7: 前端 WsClient 实现

**Files:**
- Create: `web-client/src/websocket/client.ts`
- Create: `web-client/src/websocket/index.ts`
- Create: `web-client/src/composables/useWebSocket.ts`

- [ ] **Step 1: 实现 WsClient**

```typescript
// web-client/src/websocket/client.ts

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

  // 重试延迟：3s -> 6s -> 12s -> 24s -> 30s（最多10次）
  const RETRY_DELAYS = [3000, 6000, 12000, 24000, 30000, 30000, 30000, 30000, 30000, 30000]
  const MAX_RETRIES = 10

  function getBaseUrl() {
    return import.meta.env.VITE_API_BASE_URL?.replace('http', 'ws') || 'ws://localhost:8000'
  }

  function connect(newToken: string) {
    token = newToken
    destroyed = false
    retryCount = 0

    ws = new WebSocket(`${getBaseUrl()}/api/ws?token=${token}`)

    ws.onopen = () => {
      // 连接成功，重置重试计数
      retryCount = 0
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
      if (destroyed) return

      if (event.code === CLOSE_CODE_TOKEN_ERROR) {
        // token 错误，立即刷新，不消耗重试次数
        refreshToken()
          .then(({ access_token }) => {
            connect(access_token)
          })
          .catch(() => {
            // refresh 也失败了，彻底断开
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
```

- [ ] **Step 2: 导出**

```typescript
// web-client/src/websocket/index.ts
export { createWsClient, type WsClientOptions } from './client'
```

- [ ] **Step 3: Vue Composable**

```typescript
// web-client/src/composables/useWebSocket.ts
import { ref, onUnmounted } from 'vue'
import { createWsClient, type WsClientOptions } from '../websocket'

export function useWebSocket(options: Omit<WsClientOptions, 'refreshToken'>) {
  const isConnected = ref(false)
  const messages = ref<any[]>([])

  // 复用 api/index.js 的 token 刷新逻辑
  const refreshToken = async () => {
    const refresh_token = localStorage.getItem('refresh_token')
    if (!refresh_token) throw new Error('No refresh token')

    const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/api/auth/refresh`, {
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
```

- [ ] **Step 4: 提交**

```bash
git add web-client/src/websocket/ web-client/src/composables/useWebSocket.ts
git commit -m "feat(P7): add frontend WebSocket client and Vue composable"
```

---

## Task 8: 集成测试

**Files:**
- 创建集成测试验证整个流程

- [ ] **Step 1: 提交所有代码后运行构建验证**

```bash
cd e:/code/myBlog/apps/web-client && npm run build
cd e:/code/myBlog/apps/admin-client && npm run build
```

---

## 依赖关系

```
Task 1 (ConnectionManager) ──┬── Task 2 (Router) ──── Task 3 (Consumer)
                             │                      │
                             └─── Task 4 (Tasks) ───┘
                                                      │
Task 5 (Publish Events) ─────────────────────────────┤
                                                      │
Task 6 (Admin API) ──────────────────────────────────┤
                                                      │
Task 7 (Frontend) ───────────────────────────────────┘
```

**建议执行顺序：** Task 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8
