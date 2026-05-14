# P3: Comment System Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Nested comment system with tree display (like Douyin "楼中楼" style), supporting up to 3 levels of replies.

**Architecture:**
- Single table with `parent_id` + `root_id` for efficient nested query
- `root_id` allows fetching all replies in one query, assemble tree in memory
- Max 3 levels: beyond level 3, replies are collapsed (click to expand)
- Sorting: latest (by create_time) and hottest (weighted by likes + replies)
- Soft delete: `status` field instead of physical delete

**Tech Stack:** FastAPI + SQLAlchemy async + PostgreSQL + Vue 3 + Pinia

---

## Backend: Comment CRUD

### Task 1: Comment Models & Schemas

**Files:**
- Create: `backend/apps/comments/__init__.py`
- Create: `backend/apps/comments/models.py`
- Create: `backend/apps/comments/schemas.py`
- Modify: `backend/apps/__init__.py`
- Test: `backend/tests/apps/comments/test_models.py`

- [x] **Step 1: Create backend/apps/comments/__init__.py**

```python
```

- [x] **Step 2: Create backend/apps/comments/models.py**

```python
import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, Text, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from core.database import Base


class Comment(Base):
    __tablename__ = "comments"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    blog_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("blogs.id"), nullable=False, index=True)
    author_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    parent_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), ForeignKey("comments.id"), nullable=True)
    root_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True, index=True)  # 根评论ID，便于一次拉取所有回复
    level: Mapped[int] = mapped_column(Integer, default=0)  # 0=一级评论, 1=二级, 2=三级
    like_count: Mapped[int] = mapped_column(Integer, default=0)
    reply_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[int] = mapped_column(Integer, default=1)  # 1=正常, 0=删除, 2=审核中
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(), onupdate=lambda: datetime.now())

    @property
    def is_deleted(self) -> bool:
        return self.status == 0
```

- [x] **Step 3: Create backend/apps/comments/schemas.py**

```python
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional


class CommentCreate(BaseModel):
    blog_id: str
    content: str = Field(..., min_length=1, max_length=2000)
    parent_id: Optional[str] = None  # 回复某条评论


class CommentUpdate(BaseModel):
    content: Optional[str] = Field(None, min_length=1, max_length=2000)


class CommentOut(BaseModel):
    id: str
    blog_id: str
    author_id: str
    author_username: str
    content: str
    parent_id: Optional[str]
    root_id: Optional[str]
    level: int
    like_count: int
    reply_count: int
    status: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CommentTreeOut(CommentOut):
    """带嵌套子评论的输出"""
    children: list["CommentTreeOut"] = []
    is_expanded: bool = False  # 是否展开深层回复
```

- [x] **Step 4: Create backend/tests/apps/comments/test_models.py**

```python
import pytest
from apps.comments.models import Comment


class TestCommentModel:
    def test_comment_create(self):
        comment = Comment(
            blog_id="blog-uuid",
            author_id="user-uuid",
            content="Test comment",
            level=0,
        )
        assert comment.level == 0
        assert comment.status == 1
        assert comment.like_count == 0

    def test_soft_delete(self):
        comment = Comment(
            blog_id="blog-uuid",
            author_id="user-uuid",
            content="Test comment",
        )
        comment.status = 0
        assert comment.is_deleted is True
```

- [x] **Step 5: Commit**

---

### Task 2: Comment Services & Business Logic

**Files:**
- Create: `backend/apps/comments/services.py`
- Test: `backend/tests/apps/comments/test_services.py`

- [x] **Step 1: Create backend/apps/comments/services.py**

```python
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from apps.comments.models import Comment
from apps.comments.schemas import CommentCreate, CommentUpdate


class CommentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_comment(self, comment_data: CommentCreate, author_id: str) -> Comment:
        """创建评论，支持嵌套回复"""
        parent_id = comment_data.parent_id
        level = 0
        root_id = None

        if parent_id:
            # 获取父评论，确定层级
            parent = await self.get_comment_by_id(parent_id)
            if not parent:
                raise ValueError("Parent comment not found")
            level = parent.level + 1
            if level > 2:  # 限制最大3层
                raise ValueError("Maximum reply level exceeded")
            root_id = parent.root_id or parent.id  # 使用父的root_id，或父自身

        comment = Comment(
            blog_id=comment_data.blog_id,
            author_id=author_id,
            content=comment_data.content,
            parent_id=parent_id,
            root_id=root_id,
            level=level,
        )
        self.db.add(comment)

        # 更新父评论的回复数
        if parent_id:
            parent = await self.get_comment_by_id(parent_id)
            if parent:
                parent.reply_count += 1

        await self.db.flush()
        await self.db.refresh(comment)
        return comment

    async def get_comment_by_id(self, comment_id: str) -> Optional[Comment]:
        result = await self.db.execute(
            select(Comment).where(Comment.id == comment_id, Comment.status != 0)
        )
        return result.scalar_one_or_none()

    async def get_comments_by_blog(
        self,
        blog_id: str,
        skip: int = 0,
        limit: int = 20,
        sort: str = "latest",  # "latest" or "hottest"
    ) -> list[Comment]:
        """获取博客的所有一级评论"""
        query = select(Comment).where(
            Comment.blog_id == blog_id,
            Comment.parent_id.is_(None),  # 只查一级评论
            Comment.status != 0
        )

        if sort == "hottest":
            query = query.order_by(Comment.like_count.desc(), Comment.created_at.desc())
        else:
            query = query.order_by(Comment.created_at.desc())

        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_replies(
        self,
        root_id: str,
        skip: int = 0,
        limit: int = 10,
    ) -> list[Comment]:
        """获取某个根评论下的所有回复（按层级组装）"""
        query = select(Comment).where(
            Comment.root_id == root_id,
            Comment.status != 0
        ).order_by(Comment.created_at.asc())

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def delete_comment(self, comment_id: str, author_id: str) -> bool:
        """软删除评论"""
        comment = await self.get_comment_by_id(comment_id)
        if not comment or comment.author_id != author_id:
            return False
        comment.status = 0
        await self.db.flush()
        return True

    async def build_comment_tree(self, root_id: str) -> list[dict]:
        """构建评论树（内存中组装层级）"""
        replies = await self.get_replies(root_id, skip=0, limit=100)

        # 按 parent_id 分组
        children_map = {}
        for reply in replies:
            parent = reply.parent_id
            if parent not in children_map:
                children_map[parent] = []
            children_map[parent].append(reply)

        def build_tree(comment_id: str, level: int = 1) -> list[dict]:
            children = children_map.get(comment_id, [])
            result = []
            for child in children:
                node = {
                    "id": child.id,
                    "content": child.content,
                    "author_id": child.author_id,
                    "level": child.level,
                    "like_count": child.like_count,
                    "reply_count": child.reply_count,
                    "created_at": child.created_at,
                    "children": build_tree(child.id, level + 1) if level < 2 else [],
                }
                result.append(node)
            return result

        return build_tree(root_id)
```

- [x] **Step 2: Run tests**

- [x] **Step 3: Commit**

---

### Task 3: Comment API Views

**Files:**
- Create: `backend/apps/comments/router.py`
- Modify: `backend/main.py`
- Test: `backend/tests/apps/comments/test_router.py`

- [x] **Step 1: Create backend/apps/comments/router.py**

```python
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from core.database import get_db
from core.dependencies import get_current_user
from apps.users.models import User
from apps.comments.schemas import CommentCreate, CommentUpdate, CommentOut, MessageResponse
from apps.comments.services import CommentService

router = APIRouter(prefix="/api/comments", tags=["评论"])


@router.post("", response_model=CommentOut, status_code=status.HTTP_201_CREATED)
async def create_comment(
    comment_data: CommentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = CommentService(db)
    try:
        comment = await service.create_comment(comment_data, author_id=current_user.id)
        return comment
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/blog/{blog_id}", response_model=list[CommentOut])
async def get_blog_comments(
    blog_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    sort: str = Query("latest", regex="^(latest|hottest)$"),
    db: AsyncSession = Depends(get_db),
):
    service = CommentService(db)
    comments = await service.get_comments_by_blog(blog_id, skip, limit, sort)
    return comments


@router.get("/{comment_id}/replies", response_model=list[CommentOut])
async def get_comment_replies(
    comment_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    service = CommentService(db)
    replies = await service.get_replies(comment_id, skip, limit)
    return replies


@router.delete("/{comment_id}", response_model=MessageResponse)
async def delete_comment(
    comment_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = CommentService(db)
    deleted = await service.delete_comment(comment_id, author_id=current_user.id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")
    return MessageResponse(message="Comment deleted successfully")
```

- [x] **Step 2: Register router in main.py**

```python
from apps.comments.router import router as comments_router
app.include_router(comments_router)
```

- [x] **Step 3: Commit**

---

## Frontend: Comment UI

### Task 4: Comment API Client & Store

**Files:**
- Create: `web-client/src/api/comments.js`
- Create: `web-client/src/stores/comments.js`

- [x] **Step 1: Create web-client/src/api/comments.js**

```javascript
import client from './index'

export const commentApi = {
  createComment(data) {
    return client.post('/api/comments', data)
  },

  getBlogComments(blogId, params) {
    return client.get(`/api/comments/blog/${blogId}`, { params })
  },

  getCommentReplies(commentId, params) {
    return client.get(`/api/comments/${commentId}/replies`, { params })
  },

  deleteComment(commentId) {
    return client.delete(`/api/comments/${commentId}`)
  },
}
```

- [x] **Step 2: Create web-client/src/stores/comments.js**

```javascript
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { commentApi } from '@/api/comments'

export const useCommentStore = defineStore('comments', () => {
  const comments = ref([])
  const isLoading = ref(false)

  async function fetchBlogComments(blogId, params = {}) {
    isLoading.value = true
    try {
      const response = await commentApi.getBlogComments(blogId, params)
      comments.value = response.data
    } finally {
      isLoading.value = false
    }
  }

  async function createComment(data) {
    const response = await commentApi.createComment(data)
    return response.data
  }

  async function deleteComment(commentId) {
    await commentApi.deleteComment(commentId)
    comments.value = comments.value.filter(c => c.id !== commentId)
  }

  return {
    comments,
    isLoading,
    fetchBlogComments,
    createComment,
    deleteComment,
  }
})
```

- [x] **Step 3: Commit**

---

### Task 5: Comment Component

**Files:**
- Create: `web-client/src/components/CommentSection.vue`
- Create: `web-client/src/components/CommentItem.vue`

- [x] **Step 1: Create web-client/src/components/CommentSection.vue**

```vue
<template>
  <div class="comment-section">
    <h3 class="comment-title">评论 {{ totalCount }}</h3>

    <!-- 发布评论 -->
    <div class="comment-form">
      <textarea
        v-model="newComment"
        placeholder="写下你的评论..."
        class="comment-input"
        rows="3"
      ></textarea>
      <button class="btn btn-primary" @click="handleSubmit" :disabled="!newComment.trim()">
        发布
      </button>
    </div>

    <!-- 排序切换 -->
    <div class="comment-tabs">
      <button
        :class="{ active: sort === 'latest' }"
        @click="switchSort('latest')"
      >最新</button>
      <button
        :class="{ active: sort === 'hottest' }"
        @click="switchSort('hottest')"
      >最热</button>
    </div>

    <!-- 评论列表 -->
    <div class="comment-list">
      <CommentItem
        v-for="comment in commentStore.comments"
        :key="comment.id"
        :comment="comment"
        @reply="handleReply"
        @delete="handleDelete"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useCommentStore } from '@/stores/comments'
import CommentItem from './CommentItem.vue'

const props = defineProps({
  blogId: { type: String, required: true }
})

const commentStore = useCommentStore()
const newComment = ref('')
const sort = ref('latest')

onMounted(() => {
  commentStore.fetchBlogComments(props.blogId)
})

function switchSort(newSort) {
  sort.value = newSort
  commentStore.fetchBlogComments(props.blogId, { sort: newSort })
}

async function handleSubmit() {
  if (!newComment.value.trim()) return
  await commentStore.createComment({
    blog_id: props.blogId,
    content: newComment.value,
  })
  newComment.value = ''
  commentStore.fetchBlogComments(props.blogId, { sort: sort.value })
}

function handleReply(parentId) {
  // 滚动到评论输入框
}

async function handleDelete(commentId) {
  await commentStore.deleteComment(commentId)
}
</script>

<style scoped>
.comment-section { padding: 24px; background: #FFFFFF; border-radius: 16px; }
.comment-title { font-size: 18px; font-weight: 600; margin-bottom: 16px; }
.comment-form { display: flex; gap: 12px; margin-bottom: 24px; }
.comment-input {
  flex: 1; padding: 12px; border: 1px solid #DDEEE5; border-radius: 8px;
  font-size: 14px; resize: vertical; font-family: inherit;
}
.comment-input:focus { outline: none; border-color: #5A9672; }
.comment-tabs { display: flex; gap: 16px; margin-bottom: 16px; }
.comment-tabs button {
  padding: 4px 12px; border: none; background: transparent;
  color: #6B7D72; cursor: pointer; font-size: 14px;
}
.comment-tabs button.active { color: #5A9672; font-weight: 600; border-bottom: 2px solid #5A9672; }
.comment-list { display: flex; flex-direction: column; gap: 16px; }
.btn-primary {
  padding: 8px 16px; background: #5A9672; color: white;
  border: none; border-radius: 8px; cursor: pointer;
}
.btn-primary:disabled { opacity: 0.5; }
</style>
```

- [x] **Step 2: Create web-client/src/components/CommentItem.vue**

```vue
<template>
  <div class="comment-item" :style="{ marginLeft: level * 24 + 'px' }">
    <div class="comment-header">
      <span class="comment-author">{{ comment.author_username }}</span>
      <span class="comment-time">{{ formatDate(comment.created_at) }}</span>
    </div>
    <div class="comment-content">{{ comment.content }}</div>
    <div class="comment-actions">
      <button @click="showReplyInput = !showReplyInput">回复</button>
      <span>{{ comment.like_count }} 点赞</span>
      <button v-if="canDelete" @click="$emit('delete', comment.id)">删除</button>
    </div>

    <!-- 回复输入框 -->
    <div v-if="showReplyInput" class="reply-input">
      <input v-model="replyContent" placeholder="写下你的回复..." />
      <button @click="submitReply">发送</button>
    </div>

    <!-- 子评论 -->
    <div v-if="comment.children && comment.children.length" class="comment-children">
      <CommentItem
        v-for="child in comment.children"
        :key="child.id"
        :comment="child"
        :level="level + 1"
        @reply="$emit('reply', $event)"
        @delete="$emit('delete', $event)"
      />
    </div>

    <!-- 查看更多回复 -->
    <button v-if="hasMoreReplies && !expanded" @click="loadReplies" class="load-more">
      查看 {{ replyCount }} 条回复
    </button>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useAuthStore } from '@/stores/auth'

const props = defineProps({
  comment: { type: Object, required: true },
  level: { type: Number, default: 0 },
})

const emit = defineEmits(['reply', 'delete'])
const authStore = useAuthStore()
const showReplyInput = ref(false)
const replyContent = ref('')
const expanded = ref(false)

const hasMoreReplies = computed(() => props.comment.reply_count > 0)
const replyCount = computed(() => props.comment.reply_count)
const canDelete = computed(() => props.comment.author_id === authStore.user?.id)

function formatDate(dateStr) {
  return new Date(dateStr).toLocaleDateString('zh-CN')
}

function submitReply() {
  emit('reply', { parentId: props.comment.id, content: replyContent.value })
  showReplyInput.value = false
  replyContent.value = ''
}

function loadReplies() {
  expanded.value = true
  emit('reply', { parentId: props.comment.id, loadReplies: true })
}
</script>

<style scoped>
.comment-item {
  padding: 16px; background: #F9FAFA; border-radius: 12px; margin-bottom: 12px;
}
.comment-header { display: flex; gap: 8px; margin-bottom: 8px; }
.comment-author { font-weight: 600; color: #2D3B30; font-size: 14px; }
.comment-time { color: #6B7D72; font-size: 12px; }
.comment-content { color: #2D3B30; line-height: 1.6; margin-bottom: 8px; }
.comment-actions { display: flex; gap: 16px; font-size: 13px; color: #6B7D72; }
.comment-actions button { color: #6B7D72; background: none; border: none; cursor: pointer; }
.comment-children { margin-top: 12px; }
.load-more {
  background: none; border: none; color: #5A9672; cursor: pointer; font-size: 13px; margin-top: 8px;
}
</style>
```

- [ ] **Step 3: Commit**

---

- [x] **Step 3: Commit**

----

## Self-Review Checklist

- [x] **Spec coverage:** All comment operations (create, read, delete) have tasks. Nested replies (up to 3 levels) covered.
- [x] **Placeholder scan:** No "TBD", "TODO", or vague steps found.
- [x] **Type consistency:** Comment schemas match across backend and frontend.
- [x] **Security:** Delete requires author_id check. Soft delete preserves data integrity.
- [x] **No placeholder code:** Every step shows actual implementation code.
