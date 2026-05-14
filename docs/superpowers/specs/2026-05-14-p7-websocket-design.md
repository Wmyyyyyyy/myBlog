# WebSocket 实时推送设计

## 1. 概述

WebSocket 用于实时推送用户动态流事件（博客发布、点赞、关注），支持多设备同时在线，并提供 Admin 后台在线用户统计。

**技术栈：**
- FastAPI 原生 WebSocket
- Redis Pub/Sub（已部署）
- JWT 认证（复用现有）

---

## 2. 核心流程

### 2.1 连接建立

1. 客户端连接 `/ws?token={jwt}`
2. 服务端解码 JWT 获取 `user_id`
3. 注册连接（支持多设备：`Dict[user_id, List[WebSocket]]`）
4. 设置 Redis key `ws:online:{user_id}`，TTL 60s

### 2.2 心跳保活

- 客户端每 30s 发送：`{"type": "ping"}`
- 服务端响应：`{"type": "pong"}`
- 每次心跳刷新 Redis TTL

### 2.3 连接清理

- 后台 asyncio 任务每 30s 扫描本进程所有连接
- 超过 60s 无心跳的连接强制关闭
- Redis key 过期（60s TTL）标记离线

### 2.4 动态事件发布

1. 用户发新动态 → 查粉丝 ID 列表
2. 发布到 Redis Channel `dynamic_events`，包含 `target_user_ids`
3. 各 worker 收到后推送给在线粉丝

### 2.5 Admin 在线用户

- `GET /api/admin/dashboard/online-users` 返回在线人数
- 实现：Redis `SCAN ws:online:*` 计数

---

## 3. 消息格式

### 3.1 客户端 → 服务端

```json
// 心跳
{"type": "ping"}
```

### 3.2 服务端 → 客户端

```json
// 动态事件推送
{
  "type": "dynamic",
  "event_type": "blog_post",
  "user_id": "作者ID",
  "data": {
    "target_id": "博客ID",
    "target_title": "博客标题"
  }
}

// 心跳响应
{"type": "pong"}

// 连接关闭（带原因码）
// code: 4001 = token 相关错误
```

### 3.3 Redis Pub/Sub 消息格式

```json
{
  "type": "dynamic",
  "event_type": "blog_post",
  "user_id": "作者ID",
  "data": {},
  "target_user_ids": [101, 102, 103]
}
```

---

## 4. 重连策略

**指数退避：**
- 3s → 6s → 12s → 24s → 30s（最多 10 次）

**Token 刷新：**
- 收到 code 4001（token 错误）时，立即调用 `refreshToken()`
- 刷新成功：用新 token 重连，不消耗重试次数
- 刷新失败：彻底断开，跳转登录页

---

## 5. 安全设计

### 5.1 认证

- 连接时验证 JWT，有效期内的 token 才能建立连接
- 从 token 的 `sub` 字段获取 user_id，禁止 URL 参数传递 user_id

### 5.2 连接关闭码约定

| Code | 含义 |
|------|------|
| 4001 | Token 相关错误（过期/无效） |
| 4002 | 用户被封禁 |
| 4003 | 服务器内部错误 |

---

## 6. 组件设计

### 6.1 ConnectionManager

```python
class ConnectionManager:
    connections: Dict[int, List[WebSocket]]  # user_id -> 连接列表（支持多设备）
    last_heartbeat: Dict[WebSocket, float]  # 连接 -> 最后活跃时间

    async def connect(self, ws: WebSocket, user_id: int): ...
    async def disconnect(self, ws: WebSocket, user_id: int): ...
    async def heartbeat(self, ws: WebSocket, user_id: int): ...
    async def broadcast_to_users(self, user_ids: List[int], message: dict): ...
    async def purge_inactive(self): ...  # 后台清理任务
```

### 6.2 Redis 在线状态

- Key: `ws:online:{user_id}`
- Value: `"1"`
- TTL: 60s
- 心跳时刷新 TTL

### 6.3 Redis Pub/Sub

- Channel: `dynamic_events`
- 每个 worker 订阅同一 channel
- 收到消息后根据 `target_user_ids` 推送给对应在线用户

---

## 7. Admin API

```
GET /api/admin/dashboard/online-users

Response:
{
  "online_count": 42
}
```

实现方式：Redis SCAN 统计 `ws:online:*` 数量。

---

## 8. 前端 WebSocket 客户端

### 8.1 接口设计

```typescript
interface WsClientOptions {
  token: string
  onMessage: (data: any) => void
  onClose?: (code: number) => void
  onError?: (error: Event) => void
  refreshToken: () => Promise<{ access_token: string, refresh_token: string }>
}

function createWsClient(options: WsClientOptions): WsClient
```

### 8.2 重连逻辑

1. 断线后按指数退避重连
2. 收到 4001：立即调用 `refreshToken()`，成功则用新 token 重连
3. 重试耗尽或 `refreshToken` 失败：通知业务层（跳转登录）

---

## 9. 文件结构

```
backend/
├── apps/
│   └── websocket/
│       ├── __init__.py
│       ├── manager.py       # ConnectionManager
│       ├── router.py        # WebSocket 路由
│       ├── consumer.py      # Redis Pub/Sub 消费者
│       └── tasks.py         # 后台清理任务
└── main.py                  # 注册路由

web-client/src/
├── websocket/
│   ├── client.ts            # WsClient 实现
│   └── index.ts             # 导出
└── composables/
    └── useWebSocket.ts      # Vue composable
```

---

## 10. 与现有系统集成

### 10.1 动态事件触发

在以下服务方法末尾发布 Redis 消息：

- `InteractionService.add_like()` → `blog_post` 事件
- `InteractionService.follow()` → `follow_user` 事件
- `BlogService.create_blog()` → `blog_post` 事件

### 10.2 token 刷新复用

前端 WebSocket 复用 `api/index.js` 中的 axios 拦截器 token 刷新逻辑：
- 从 `localStorage` 取 `refresh_token`
- 发请求到 `/api/auth/refresh`
- 更新 `localStorage` 中的 token
