# P4: Interactions + Dynamics 设计规格书

> **Status:** Draft — 待实现前审核

## 1. 架构设计

### 1.1 事件驱动架构

采用**单向事件流**设计：

```
interactions / blogs / foundation (产生事件)
         ↓
    DynamicEvent (统一存储)
         ↓
    dynamics (查询消费)
```

**边界划分**：
- `interactions` — 点赞/收藏/关注操作，写事件到 dynamics
- `blogs` — 发布博客，写事件到 dynamics
- `foundation` — 打卡，写事件到 dynamics
- `dynamics` — 只负责存储和查询 DynamicEvent，不产生事件

**优点**：模块解耦，新增事件类型不影响现有模块

### 1.2 数据模型

#### DynamicEvent

```python
class DynamicEvent(Base):
    __tablename__ = "dynamic_events"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True)
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)  # blog_post/like_blog/favorite_blog/follow/checkin
    target_id: Mapped[str] = mapped_column(String(255), nullable=True)  # 博客ID/用户ID/成就ID
    target_title: Mapped[str] = mapped_column(String(255), nullable=True)  # 博客标题/成就名称
    target_user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=True)  # 关联对象作者
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now())
```

**索引**：
- `idx_dynamic_user_created` — `(user_id, created_at)` 用户动态
- `idx_dynamic_created` — `(created_at, id)` 全局排序

#### Interactions

```python
class Favorite(Base):
    __tablename__ = "favorites"
    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True)
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    blog_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("blogs.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now())
    __table_args__ = UniqueConstraint('user_id', 'blog_id', name='uq_user_blog_favorite')

class Like(Base):
    __tablename__ = "likes"
    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True)
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    blog_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("blogs.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now())
    __table_args__ = UniqueConstraint('user_id', 'blog_id', name='uq_user_blog_like')

class Follow(Base):
    __tablename__ = "follows"
    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True)
    follower_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)  # 关注者
    following_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)  # 被关注者
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now())
    __table_args__ = UniqueConstraint('follower_id', 'following_id', name='uq_follower_following')
```

---

## 2. API 设计

### 2.1 Interactions API

#### 收藏

| 接口 | 方法 | 说明 | 认证 |
|------|------|------|------|
| `/api/interactions/favorites/{blog_id}` | POST | 收藏博客 | 需要 |
| `/api/interactions/favorites/{blog_id}` | DELETE | 取消收藏 | 需要 |
| `/api/interactions/favorites/{blog_id}/status` | GET | 检查收藏状态 | 需要 |
| `/api/interactions/favorites` | GET | 我的收藏列表（分页） | 需要 |

#### 点赞

| 接口 | 方法 | 说明 | 认证 |
|------|------|------|------|
| `/api/interactions/likes/{blog_id}` | POST | 点赞博客 | 需要 |
| `/api/interactions/likes/{blog_id}` | DELETE | 取消点赞 | 需要 |
| `/api/interactions/likes/{blog_id}/status` | GET | 检查点赞状态 | 需要 |

#### 关注

| 接口 | 方法 | 说明 | 认证 |
|------|------|------|------|
| `/api/interactions/follows/{user_id}` | POST | 关注用户 | 需要 |
| `/api/interactions/follows/{user_id}` | DELETE | 取消关注 | 需要 |
| `/api/interactions/follows/{user_id}/status` | GET | 检查关注状态 | 需要 |
| `/api/interactions/followers/{user_id}` | GET | 粉丝列表（分页） | 可选 |
| `/api/interactions/following/{user_id}` | GET | 关注列表（分页） | 可选 |

### 2.2 Dynamics API

| 接口 | 方法 | 说明 | 认证 |
|------|------|------|------|
| `/api/dynamics/feed` | GET | 我的动态流（分页游标） | 需要 |
| `/api/dynamics/user/{user_id}` | GET | 他人动态（分页） | 可选 |

#### Feed 响应格式

```json
{
  "events": [
    {
      "id": "uuid",
      "event_type": "blog_post",
      "user_id": "xxx",
      "user_username": "张三",
      "user_avatar": "url",
      "target_id": "博客uuid",
      "target_title": "我的第一篇博客",
      "target_user_id": "xxx",
      "target_user_username": "张三",
      "created_at": "2026-05-14T10:00:00Z"
    }
  ],
  "next_cursor": {
    "created_at": "2026-05-14T09:00:00Z",
    "id": "uuid"
  }
}
```

---

## 3. 分页设计

### 3.1 游标分页

采用**时间戳+ID 复合游标**，防止重复拉取和漏数据。

**请求参数**：
```
GET /api/dynamics/feed?cursor=<encoded_cursor>&limit=20
```

**游标结构**：
```json
{
  "created_at": "2026-05-14T10:00:00Z",
  "id": "uuid-xxx"
}
```

**查询逻辑**：
```sql
WHERE (created_at, id) < (cursor.created_at, cursor.id)
ORDER BY created_at DESC, id DESC
LIMIT 20
```

### 3.2 限制

- 默认每页 20 条
- 最大每页 50 条
- 只查询最近 30 天动态（防止数据膨胀）

---

## 4. 限流设计

### 4.1 策略

- **用户维度**（不考虑 IP）
- **固定窗口 1 分钟**（Redis INCR + EXPIRE）
- 滑动窗口计数超限返回 `429 Too Many Requests`

### 4.2 限制值

| 接口类型 | 限制 |
|----------|------|
| Feed 拉取 | 30 次/分钟 |
| 写操作（点赞/关注/收藏） | 20 次/分钟 |
| 其他读接口 | 60 次/分钟 |

### 4.3 Redis Key 格式

```
rate_limit:{user_id}:{endpoint}:{minute_timestamp}
```

### 4.4 响应头

```
429 Too Many Requests
Retry-After: 60
X-RateLimit-Limit: 30
X-RateLimit-Remaining: 0
```

---

## 5. 事件记录时机

| 事件 | 触发位置 | 记录到 dynamics |
|------|----------|-----------------|
| 发布博客 | blogs/services.py | ✓ |
| 点赞博客 | interactions/services.py | ✓ |
| 收藏博客 | interactions/services.py | ✓ |
| 关注用户 | interactions/services.py | ✓ |
| 打卡 | foundation/services.py | ✓（P5） |

---

## 6. WebSocket 后续规划

**状态**：暂不实现，作为独立任务后续开发

**需要的功能**：
- 用户上线时建立 WebSocket 连接
- 新动态时主动推送给在线粉丝
- Redis Pub/Sub 多 worker 同步
- 心跳保活 + 重连处理

**TODO 清单**：
- [ ] WebSocket 连接管理
- [ ] Redis Pub/Sub 集成
- [ ] 客户端 SDK
- [ ] 推送性能优化（粉丝量大时）

---

## 7. 安全考虑

- 关注/取消关注需验证不能关注自己
- 收藏/点赞需验证博客是否存在
- 动态流只展示公开状态的内容
- 限流防止恶意刷取

---

## 8. 测试场景

1. 用户 A 关注用户 B，用户 B 发布博客，用户 A 的 feed 能看到
2. 用户 A 点赞博客，动态记录正确
3. 限流：30 次/分钟内正常，超过返回 429
4. 游标分页：正常翻页，边界情况处理
5. 重复点赞/关注：返回已存在，不报错
