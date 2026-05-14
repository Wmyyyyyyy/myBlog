# P4: Interactions + Dynamics Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Favorites, likes, follows, and user dynamics feed with cursor pagination and rate limiting.

**Architecture:**
- Interactions: Favorite, Like, Follow models + write events to dynamics
- Dynamics: DynamicEvent model + query feed
- Rate limiting: Redis INCR + EXPIRE, user-dimension
- WebSocket: NOT implemented (P4.5 future work)

**Tech Stack:** FastAPI + SQLAlchemy async + PostgreSQL + Redis + Vue 3 + Pinia

---

## Backend: Interactions

### Task 1: Interactions Models & Schemas

**Files:**
- Modify: `backend/apps/interactions/__init__.py`
- Modify: `backend/apps/interactions/models.py`
- Create: `backend/apps/interactions/schemas.py`
- Modify: `backend/apps/__init__.py`
- Test: `backend/tests/apps/interactions/test_models.py`

- [ ] **Step 1: Update backend/apps/interactions/models.py (if needed)**

Check existing models match design:
- Favorite: user_id, blog_id, created_at, unique constraint
- Like: user_id, blog_id, created_at, unique constraint
- Follow: follower_id, following_id, created_at, unique constraint

- [ ] **Step 2: Create backend/apps/interactions/schemas.py**

```python
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional


class FavoriteCreate(BaseModel):
    blog_id: str


class FavoriteOut(BaseModel):
    id: str
    user_id: str
    blog_id: str
    created_at: datetime

    model_config = {"from_attributes": True}


class FavoriteStatus(BaseModel):
    is_favorited: bool
    favorite_count: int


class LikeCreate(BaseModel):
    blog_id: str


class LikeOut(BaseModel):
    id: str
    user_id: str
    blog_id: str
    created_at: datetime

    model_config = {"from_attributes": True}


class LikeStatus(BaseModel):
    is_liked: bool
    like_count: int


class FollowCreate(BaseModel):
    user_id: str  # the user to follow


class FollowOut(BaseModel):
    id: str
    follower_id: str
    following_id: str
    created_at: datetime

    model_config = {"from_attributes": True}


class FollowStatus(BaseModel):
    is_following: bool


class FollowerOut(BaseModel):
    id: str
    username: str
    avatar: Optional[str]
    followed_at: datetime


class FollowingOut(BaseModel):
    id: str
    username: str
    avatar: Optional[str]
    followed_at: datetime


class MessageResponse(BaseModel):
    message: str
```

- [ ] **Step 3: Run tests**

```bash
cd backend && .venv/Scripts/python.exe -m pytest tests/apps/interactions/test_models.py -v
```

- [ ] **Step 4: Commit**

---

### Task 2: Interactions Services & Business Logic

**Files:**
- Modify: `backend/apps/interactions/services.py`
- Test: `backend/tests/apps/interactions/test_services.py`

- [ ] **Step 1: Update backend/apps/interactions/services.py**

Key methods:
- `add_favorite(user_id, blog_id)` — add favorite, write to dynamics
- `remove_favorite(user_id, blog_id)` — remove favorite
- `check_favorite_status(user_id, blog_id)` — check if favorited
- `get_user_favorites(user_id, skip, limit)` — paginated favorites
- `add_like(user_id, blog_id)` — add like, write to dynamics, get blog author
- `remove_like(user_id, blog_id)` — remove like
- `check_like_status(user_id, blog_id)` — check if liked
- `add_follow(follower_id, following_id)` — add follow, write to dynamics
- `remove_follow(follower_id, following_id)` — remove follow
- `check_follow_status(follower_id, following_id)` — check if following
- `get_followers(user_id, skip, limit)` — paginated followers
- `get_following(user_id, skip, limit)` — paginated following

**Important:** When adding like/favorite/follow, write to dynamics:
```python
from apps.dynamics.services import DynamicService

async def add_like(user_id: str, blog_id: str) -> Like:
    # ... existing logic ...
    # Write to dynamics
    dynamic_service = DynamicService(self.db)
    await dynamic_service.record_like_blog(
        user_id=user_id,
        blog_id=blog_id,
        target_user_id=blog.author_id  # blog author for display
    )
```

- [ ] **Step 2: Run tests**

```bash
cd backend && .venv/Scripts/python.exe -m pytest tests/apps/interactions/test_services.py -v
```

- [ ] **Step 3: Commit**

---

### Task 3: Interactions API Views

**Files:**
- Modify: `backend/apps/interactions/router.py`
- Modify: `backend/main.py`
- Test: `backend/tests/apps/interactions/test_router.py`

- [ ] **Step 1: Update backend/apps/interactions/router.py**

Endpoints:
- `POST /api/interactions/favorites/{blog_id}` — add favorite
- `DELETE /api/interactions/favorites/{blog_id}` — remove favorite
- `GET /api/interactions/favorites/{blog_id}/status` — check favorite status
- `GET /api/interactions/favorites` — my favorites (paginated)
- `POST /api/interactions/likes/{blog_id}` — add like
- `DELETE /api/interactions/likes/{blog_id}` — remove like
- `GET /api/interactions/likes/{blog_id}/status` — check like status
- `POST /api/interactions/follows/{user_id}` — follow user
- `DELETE /api/interactions/follows/{user_id}` — unfollow user
- `GET /api/interactions/follows/{user_id}/status` — check follow status
- `GET /api/interactions/followers/{user_id}` — followers (paginated)
- `GET /api/interactions/following/{user_id}` — following (paginated)

**Rate limiting:** Apply rate limit decorator for write operations.

- [ ] **Step 2: Register router in main.py (if not already registered)**

- [ ] **Step 3: Run tests**

- [ ] **Step 4: Commit**

---

## Backend: Dynamics

### Task 4: DynamicEvent Model & Schema

**Files:**
- Modify: `backend/apps/dynamics/__init__.py`
- Modify: `backend/apps/dynamics/models.py` (check existing)
- Modify: `backend/apps/dynamics/schemas.py`
- Test: `backend/tests/apps/dynamics/test_models.py`

- [ ] **Step 1: Verify backend/apps/dynamics/models.py**

Check existing DynamicEvent model matches design:
```python
class DynamicEvent(Base):
    __tablename__ = "dynamic_events"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True)
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    target_id: Mapped[str] = mapped_column(String(255), nullable=True)
    target_title: Mapped[str] = mapped_column(String(255), nullable=True)
    target_user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now())
```

Indexes:
- `idx_dynamic_user_created` — (user_id, created_at)
- `idx_dynamic_created` — (created_at, id)

- [ ] **Step 2: Update backend/apps/dynamics/schemas.py**

```python
from datetime import datetime
from pydantic import BaseModel
from typing import Optional


class DynamicEventOut(BaseModel):
    id: str
    event_type: str
    user_id: str
    user_username: str
    user_avatar: Optional[str]
    target_id: Optional[str]
    target_title: Optional[str]
    target_user_id: Optional[str]
    target_user_username: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class FeedResponse(BaseModel):
    events: list[DynamicEventOut]
    next_cursor: Optional[dict] = None  # {"created_at": "...", "id": "..."}


class CursorParams(BaseModel):
    cursor: Optional[str] = None  # URL encoded JSON
    limit: int = 20
```

- [ ] **Step 3: Run tests**

- [ ] **Step 4: Commit**

---

### Task 5: Dynamics Service & Business Logic

**Files:**
- Modify: `backend/apps/dynamics/services.py`
- Test: `backend/tests/apps/dynamics/test_services.py`

- [ ] **Step 1: Update backend/apps/dynamics/services.py**

Key methods:
- `record_blog_post(user_id, blog_id, blog_title)` — record blog post event
- `record_like_blog(user_id, blog_id, target_user_id)` — record like event
- `record_favorite_blog(user_id, blog_id, target_user_id)` — record favorite event
- `record_follow(follower_id, following_id)` — record follow event
- `record_checkin(user_id, achievement_id, achievement_name)` — record checkin event (P5)
- `get_user_feed(user_id, cursor, limit)` — paginated feed for user
- `get_user_events(user_id, cursor, limit)` — paginated events for specific user

**Cursor pagination logic:**
```python
async def get_user_feed(self, user_id: str, cursor: dict = None, limit: int = 20):
    # Get user's following list
    following = await self.get_following_ids(user_id)
    # Include self
    user_ids = following + [user_id]

    query = select(DynamicEvent).where(
        DynamicEvent.user_id.in_(user_ids),
        DynamicEvent.created_at >= datetime.now() - timedelta(days=30)  # 30 days limit
    )

    if cursor:
        query = query.where(
            or_(
                DynamicEvent.created_at < cursor['created_at'],
                and_(
                    DynamicEvent.created_at == cursor['created_at'],
                    DynamicEvent.id < cursor['id']
                )
            )
        )

    query = query.order_by(DynamicEvent.created_at.desc(), DynamicEvent.id.desc()).limit(limit)
    # ...
```

- [ ] **Step 2: Run tests**

- [ ] **Step 3: Commit**

---

### Task 6: Dynamics API Views

**Files:**
- Modify: `backend/apps/dynamics/router.py`
- Test: `backend/tests/apps/dynamics/test_router.py`

- [ ] **Step 1: Update backend/apps/dynamics/router.py**

Endpoints:
- `GET /api/dynamics/feed` — my feed (cursor pagination)
- `GET /api/dynamics/user/{user_id}` — user's events (cursor pagination)

**Cursor parsing:**
```python
from urllib.parse import unquote
import json

def parse_cursor(cursor_str: str) -> dict:
    if not cursor_str:
        return None
    return json.loads(unquote(cursor_str))
```

- [ ] **Step 2: Register router in main.py (if not already registered)**

- [ ] **Step 3: Run tests**

- [ ] **Step 4: Commit**

---

## Backend: Rate Limiting

### Task 7: Rate Limiting Middleware

**Files:**
- Create: `backend/core/rate_limit.py`
- Modify: `backend/main.py`
- Test: `backend/tests/test_rate_limit.py`

- [ ] **Step 1: Create backend/core/rate_limit.py**

```python
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from redis.asyncio import Redis
import time

# Redis key format: rate_limit:{user_id}:{endpoint}:{minute}
# Use fixed window (minute timestamp // 60)

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, redis: Redis):
        super().__init__(app)
        self.redis = redis
        self.limits = {
            "/api/dynamics/feed": 30,  # per minute
            "/api/interactions/favorites": 20,
            "/api/interactions/likes": 20,
            "/api/interactions/follows": 20,
            "default": 60
        }

    async def dispatch(self, request: Request, call_next):
        # Skip if no auth user
        user_id = getattr(request.state, 'user_id', None)
        if not user_id:
            return await call_next(request)

        # Determine limit
        path = request.url.path
        limit = self.limits.get(path, self.limits["default"])

        # Check rate limit
        minute = int(time.time()) // 60
        key = f"rate_limit:{user_id}:{path}:{minute}"

        count = await self.redis.incr(key)
        if count == 1:
            await self.redis.expire(key, 60)

        if count > limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests",
                headers={"Retry-After": "60", "X-RateLimit-Limit": str(limit)}
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(max(0, limit - count))
        return response
```

- [ ] **Step 2: Register middleware in main.py**

```python
from core.rate_limit import RateLimitMiddleware

app.add_middleware(RateLimitMiddleware, redis=redis_client)
```

- [ ] **Step 3: Run tests**

- [ ] **Step 4: Commit**

---

## Frontend: Interactions UI

### Task 8: Interactions API Client

**Files:**
- Modify: `web-client/src/api/interactions.js`
- Modify: `web-client/src/stores/interactions.js`

- [ ] **Step 1: Update web-client/src/api/interactions.js**

```javascript
import client from './index'

export const interactionApi = {
  // Favorites
  addFavorite(blogId) {
    return client.post(`/api/interactions/favorites/${blogId}`)
  },
  removeFavorite(blogId) {
    return client.delete(`/api/interactions/favorites/${blogId}`)
  },
  getFavoriteStatus(blogId) {
    return client.get(`/api/interactions/favorites/${blogId}/status`)
  },
  getMyFavorites(params) {
    return client.get('/api/interactions/favorites', { params })
  },

  // Likes
  addLike(blogId) {
    return client.post(`/api/interactions/likes/${blogId}`)
  },
  removeLike(blogId) {
    return client.delete(`/api/interactions/likes/${blogId}`)
  },
  getLikeStatus(blogId) {
    return client.get(`/api/interactions/likes/${blogId}/status`)
  },

  // Follows
  follow(userId) {
    return client.post(`/api/interactions/follows/${userId}`)
  },
  unfollow(userId) {
    return client.delete(`/api/interactions/follows/${userId}`)
  },
  getFollowStatus(userId) {
    return client.get(`/api/interactions/follows/${userId}/status`)
  },
  getFollowers(userId, params) {
    return client.get(`/api/interactions/followers/${userId}`, { params })
  },
  getFollowing(userId, params) {
    return client.get(`/api/interactions/following/${userId}`, { params })
  },
}
```

- [ ] **Step 2: Update web-client/src/stores/interactions.js**

```javascript
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { interactionApi } from '@/api/interactions'

export const useInteractionStore = defineStore('interactions', () => {
  // Favorites
  const favorites = ref([])
  const favoriteStatus = ref({})

  async function toggleFavorite(blogId) {
    const status = favoriteStatus.value[blogId]
    if (status?.is_favorited) {
      await interactionApi.removeFavorite(blogId)
    } else {
      await interactionApi.addFavorite(blogId)
    }
    await checkFavoriteStatus(blogId)
  }

  async function checkFavoriteStatus(blogId) {
    const res = await interactionApi.getFavoriteStatus(blogId)
    favoriteStatus.value[blogId] = res.data
  }

  // Likes
  const likeStatus = ref({})

  async function toggleLike(blogId) {
    const status = likeStatus.value[blogId]
    if (status?.is_liked) {
      await interactionApi.removeLike(blogId)
    } else {
      await interactionApi.addLike(blogId)
    }
    await checkLikeStatus(blogId)
  }

  async function checkLikeStatus(blogId) {
    const res = await interactionApi.getLikeStatus(blogId)
    likeStatus.value[blogId] = res.data
  }

  // Follows
  const followStatus = ref({})

  async function toggleFollow(userId) {
    const status = followStatus.value[userId]
    if (status?.is_following) {
      await interactionApi.unfollow(userId)
    } else {
      await interactionApi.follow(userId)
    }
    await checkFollowStatus(userId)
  }

  async function checkFollowStatus(userId) {
    const res = await interactionApi.getFollowStatus(userId)
    followStatus.value[userId] = res.data
  }

  return {
    favorites,
    favoriteStatus,
    toggleFavorite,
    checkFavoriteStatus,
    likeStatus,
    toggleLike,
    checkLikeStatus,
    followStatus,
    toggleFollow,
    checkFollowStatus,
  }
})
```

- [ ] **Step 3: Commit**

---

### Task 9: Interactions Components

**Files:**
- Create: `web-client/src/components/LikeButton.vue`
- Create: `web-client/src/components/FavoriteButton.vue`
- Create: `web-client/src/components/FollowButton.vue`

- [ ] **Step 1: Create LikeButton.vue**

```vue
<template>
  <button @click="handleClick" class="like-btn" :class="{ liked: isLiked }">
    <span class="icon">{{ isLiked ? '❤️' : '🤍' }}</span>
    <span class="count">{{ likeCount }}</span>
  </button>
</template>

<script setup>
import { computed } from 'vue'
import { useInteractionStore } from '@/stores/interactions'

const props = defineProps({
  blogId: { type: String, required: true },
  initialLiked: { type: Boolean, default: false },
  initialCount: { type: Number, default: 0 }
})

const interactionStore = useInteractionStore()

const isLiked = computed(() => interactionStore.likeStatus[props.blogId]?.is_liked ?? props.initialLiked)
const likeCount = computed(() => interactionStore.likeStatus[props.blogId]?.like_count ?? props.initialCount)

async function handleClick() {
  await interactionStore.toggleLike(props.blogId)
}
</script>

<style scoped>
.like-btn { display: flex; align-items: center; gap: 4px; background: none; border: none; cursor: pointer; }
.like-btn.liked { color: #e24; }
</style>
```

- [ ] **Step 2: Create FavoriteButton.vue** (similar pattern)

- [ ] **Step 3: Create FollowButton.vue** (similar pattern)

- [ ] **Step 4: Commit**

---

## Frontend: Dynamics UI

### Task 10: Dynamics API Client & Store

**Files:**
- Create: `web-client/src/api/dynamics.js`
- Create: `web-client/src/stores/dynamics.js`

- [ ] **Step 1: Create web-client/src/api/dynamics.js**

```javascript
import client from './index'

export const dynamicsApi = {
  getFeed(params) {
    return client.get('/api/dynamics/feed', { params })
  },
  getUserEvents(userId, params) {
    return client.get(`/api/dynamics/user/${userId}`, { params })
  },
}
```

- [ ] **Step 2: Create web-client/src/stores/dynamics.js**

```javascript
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { dynamicsApi } from '@/api/dynamics'

export const useDynamicsStore = defineStore('dynamics', () => {
  const events = ref([])
  const nextCursor = ref(null)
  const isLoading = ref(false)

  async function fetchFeed(reset = false) {
    if (reset) {
      events.value = []
      nextCursor.value = null
    }
    isLoading.value = true
    try {
      const params = {}
      if (nextCursor.value) {
        params.cursor = JSON.stringify(nextCursor.value)
      }
      const res = await dynamicsApi.getFeed(params)
      events.value.push(...res.data.events)
      nextCursor.value = res.data.next_cursor
    } finally {
      isLoading.value = false
    }
  }

  return {
    events,
    nextCursor,
    isLoading,
    fetchFeed,
  }
})
```

- [ ] **Step 3: Commit**

---

### Task 11: Dynamics Feed Component

**Files:**
- Create: `web-client/src/components/DynamicFeed.vue`
- Create: `web-client/src/components/DynamicItem.vue`

- [ ] **Step 1: Create DynamicItem.vue**

```vue
<template>
  <div class="dynamic-item">
    <div class="user-info">
      <img :src="event.user_avatar || defaultAvatar" class="avatar" />
      <span class="username">{{ event.user_username }}</span>
    </div>
    <div class="content">
      {{ actionText }} {{ targetText }}
    </div>
    <div class="time">{{ formatTime(event.created_at) }}</div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  event: { type: Object, required: true }
})

const defaultAvatar = '/default-avatar.png'

const actionText = computed(() => {
  const map = {
    blog_post: '发布了博客',
    like_blog: '点赞了',
    favorite_blog: '收藏了',
    follow: '关注了',
    checkin: '完成了打卡'
  }
  return map[props.event.event_type] || props.event.event_type
})

const targetText = computed(() => {
  if (props.event.target_title) {
    return `"${props.event.target_title}"`
  }
  return ''
})

function formatTime(dateStr) {
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now - date
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff/60000)}分钟前`
  if (diff < 86400000) return `${Math.floor(diff/3600000)}小时前`
  return date.toLocaleDateString('zh-CN')
}
</script>

<style scoped>
.dynamic-item { padding: 16px; background: #f9fafa; border-radius: 12px; margin-bottom: 12px; }
.user-info { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.avatar { width: 32px; height: 32px; border-radius: 50%; }
.username { font-weight: 600; color: #2d3b30; }
.content { color: #2d3b30; line-height: 1.5; }
.time { color: #6b7d72; font-size: 12px; margin-top: 8px; }
</style>
```

- [ ] **Step 2: Create DynamicFeed.vue**

```vue
<template>
  <div class="dynamic-feed">
    <h3>动态</h3>
    <div class="feed-list">
      <DynamicItem v-for="event in store.events" :key="event.id" :event="event" />
    </div>
    <div v-if="store.nextCursor" class="load-more">
      <button @click="loadMore" :disabled="store.isLoading">
        {{ store.isLoading ? '加载中...' : '加载更多' }}
      </button>
    </div>
    <div v-else-if="!store.isLoading && store.events.length === 0" class="empty">
      暂无动态
    </div>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useDynamicsStore } from '@/stores/dynamics'
import DynamicItem from './DynamicItem.vue'

const store = useDynamicsStore()

onMounted(() => {
  store.fetchFeed()
})

function loadMore() {
  store.fetchFeed()
}
</script>

<style scoped>
.dynamic-feed { padding: 16px; }
.feed-list { margin-top: 16px; }
.load-more { text-align: center; margin-top: 16px; }
.load-more button { padding: 8px 24px; background: #5a9672; color: white; border: none; border-radius: 8px; cursor: pointer; }
.load-more button:disabled { opacity: 0.5; }
.empty { text-align: center; color: #6b7d72; padding: 32px; }
</style>
```

- [ ] **Step 3: Add to profile page or create dedicated page**

- [ ] **Step 4: Commit**

---

## Integration Tasks

### Task 12: Blog Detail Page Updates

**Files:**
- Modify: `web-client/src/views/BlogDetail.vue`

- [ ] **Step 1: Add interaction buttons to BlogDetail.vue**

Add LikeButton and FavoriteButton to blog detail page.

- [ ] **Step 2: Commit**

---

### Task 13: User Profile Page Updates

**Files:**
- Modify: `web-client/src/views/Profile.vue`

- [ ] **Step 1: Add FollowButton to user profile**

- [ ] **Step 2: Add DynamicFeed to user profile**

- [ ] **Step 3: Commit**

---

## Self-Review Checklist

- [ ] **Spec coverage:** All interactions (favorite/like/follow) have CRUD tasks. Dynamics feed with cursor pagination implemented.
- [ ] **Rate limiting:** Redis-based rate limiting with configurable limits per endpoint.
- [ ] **Event recording:** Interactions write events to dynamics service.
- [ ] **No placeholder code:** Every step shows actual implementation code.
- [ ] **Type consistency:** Frontend stores match backend response formats.
