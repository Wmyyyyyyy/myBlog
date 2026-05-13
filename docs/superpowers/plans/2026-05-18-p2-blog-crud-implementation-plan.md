# P2: Blog CRUD + Sensitive Word Moderation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Blog creation/editing/deletion with DFA-based sensitive word moderation (block/replace/warn three-level actions).

**Architecture:** Backend exposes REST API for blog CRUD. DFA (Deterministic Finite Automaton) algorithm scans content before save. Three action levels: block (reject), replace (auto-censor with ****), warn (allow with flag). Frontend provides blog list, editor, and detail views.

**Tech Stack:** FastAPI · SQLAlchemy async · Pydantic v2 · DFA algorithm · Vue 3 · Pinia · Element Plus

---

## Backend: Blog CRUD

### Task 1: Blog Models & Schemas

**Files:**
- Create: `backend/apps/blogs/models.py`
- Create: `backend/apps/blogs/schemas.py`
- Modify: `backend/apps/__init__.py`
- Test: `backend/tests/apps/blogs/test_models.py`

- [ ] **Step 1: Create backend/apps/blogs/__init__.py**

```python
# apps/blogs/__init__.py
```

- [ ] **Step 2: Create backend/apps/blogs/models.py**

```python
import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, Text, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from core.database import Base


class Blog(Base):
    __tablename__ = "blogs"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    title: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    excerpt: Mapped[str | None] = mapped_column(String(500), nullable=True)
    cover_image: Mapped[str | None] = mapped_column(String(500), nullable=True)
    author_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    category: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    tags: Mapped[str | None] = mapped_column(String(200), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="published", index=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    view_count: Mapped[int] = mapped_column(Integer, default=0)
    like_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(), onupdate=lambda: datetime.now())


class Comment(Base):
    __tablename__ = "comments"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    blog_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("blogs.id"), nullable=False)
    author_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    parent_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), ForeignKey("comments.id"), nullable=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now())
```

- [ ] **Step 3: Create backend/apps/blogs/schemas.py**

```python
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from typing import Optional


class BlogCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)
    excerpt: Optional[str] = Field(None, max_length=500)
    cover_image: Optional[str] = None
    category: Optional[str] = Field(None, max_length=50)
    tags: Optional[str] = None

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Title cannot be empty")
        return v


class BlogUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    content: Optional[str] = Field(None, min_length=1)
    excerpt: Optional[str] = Field(None, max_length=500)
    cover_image: Optional[str] = None
    category: Optional[str] = Field(None, max_length=50)
    tags: Optional[str] = None
    status: Optional[str] = None


class BlogOut(BaseModel):
    id: str
    title: str
    content: str
    excerpt: Optional[str]
    cover_image: Optional[str]
    author_id: str
    category: Optional[str]
    tags: Optional[str]
    status: str
    view_count: int
    like_count: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BlogListOut(BaseModel):
    id: str
    title: str
    excerpt: Optional[str]
    cover_image: Optional[str]
    author_id: str
    author_username: str
    category: Optional[str]
    tags: Optional[str]
    status: str
    view_count: int
    like_count: int
    created_at: datetime

    model_config = {"from_attributes": True}


class ModerationResult(BaseModel):
    passed: bool
    action: str  # "block", "replace", "warn", "pass"
    original_text: str
    moderated_text: Optional[str] = None
    flagged_words: list[str] = []


class MessageResponse(BaseModel):
    message: str
```

- [ ] **Step 4: Create backend/tests/apps/blogs/test_models.py**

```python
import pytest
from apps.blogs.models import Blog, Comment


class TestBlogModel:
    def test_blog_create(self):
        blog = Blog(
            title="Test Blog",
            content="Test content",
            author_id="test-uuid",
        )
        assert blog.title == "Test Blog"
        assert blog.status == "published"
        assert blog.is_deleted is False
```

- [ ] **Step 5: Commit**

```bash
git add backend/apps/blogs/ backend/tests/apps/blogs/
git commit -m "feat: P2 blog models and schemas"
```

---

### Task 2: DFA Sensitive Word Filter

**Files:**
- Create: `backend/core/moderation.py`
- Test: `backend/tests/core/test_moderation.py`

- [ ] **Step 1: Write failing test for DFA filter**

```python
# backend/tests/core/test_moderation.py
import pytest
from core.moderation import DFAFilter, ModerationAction


class TestDFAFilter:
    def test_empty_word_list(self):
        filter = DFAFilter([])
        result = filter.check("hello world")
        assert result.passed is True

    def test_block_action(self):
        # "bad" is in word list with block action
        filter = DFAFilter([("bad", "block")])
        result = filter.check("this is bad content")
        assert result.passed is False
        assert result.action == "block"
        assert "bad" in result.flagged_words

    def test_replace_action(self):
        filter = DFAFilter([("bad", "replace")])
        result = filter.check("this is bad content")
        assert result.passed is True
        assert result.action == "replace"
        assert "****" in result.moderated_text

    def test_warn_action(self):
        filter = DFAFilter([("bad", "warn")])
        result = filter.check("this is bad content")
        assert result.passed is True
        assert result.action == "warn"

    def test_multiple_flagged_words(self):
        filter = DFAFilter([("bad", "block"), ("evil", "replace")])
        result = filter.check("this is bad and evil")
        assert result.passed is False
        assert result.action == "block"
        assert "bad" in result.flagged_words
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd backend && .venv/Scripts/python.exe -m pytest tests/core/test_moderation.py -v
# Expected: FAIL - module not found
```

- [ ] **Step 3: Write DFA filter implementation**

```python
# backend/core/moderation.py
from enum import Enum
from dataclasses import dataclass
import re


class ModerationAction(str, Enum):
    BLOCK = "block"      # Reject content
    REPLACE = "replace"  # Auto-censor with ****
    WARN = "warn"        # Allow but flag for review


@dataclass
class ModerationResult:
    passed: bool
    action: str
    original_text: str
    moderated_text: str | None
    flagged_words: list[str]

    @property
    def block(self) -> bool:
        return self.action == ModerationAction.BLOCK.value

    @property
    def replace(self) -> bool:
        return self.action == ModerationAction.REPLACE.value


class DFAFilter:
    """
    DFA (Deterministic Finite Automaton) based sensitive word filter.
    Supports three action levels: block, replace, warn.
    """

    def __init__(self, word_list: list[tuple[str, str]]):
        """
        Args:
            word_list: List of (word, action) tuples.
                      action: "block", "replace", or "warn"
        """
        self._fail_state = -1
        self._next_state = 1
        self._goto = {0: {}}  # state -> {char: next_state}
        self._output = {}      # state -> action or None
        self._states = [0]    # list of all states

        # Sort by length descending for longest-match priority
        sorted_words = sorted(word_list, key=lambda x: len(x[0]), reverse=True)

        for word, action in sorted_words:
            self._add_word(word, action)

    def _add_word(self, word: str, action: str) -> None:
        """Add a word to the DFA."""
        state = 0
        for char in word.lower():
            if char not in self._goto[state]:
                new_state = self._next_state
                self._next_state += 1
                self._goto[state][char] = new_state
                self._goto.append({})
                self._output.append(None)
                self._states.append(new_state)
                state = new_state
            else:
                state = self._goto[state][char]
        # Mark output state
        self._output[state] = action

    def check(self, text: str) -> ModerationResult:
        """
        Check text for sensitive words using DFA algorithm.
        Returns ModerationResult with action determination.
        """
        if not self._goto[0]:
            return ModerationResult(
                passed=True,
                action="pass",
                original_text=text,
                moderated_text=text,
                flagged_words=[],
            )

        flagged = []
        result_text = list(text)
        highest_action_priority = 0  # block=3, replace=2, warn=1

        i = 0
        while i < len(text):
            char = text[i].lower()
            if char not in self._goto[0]:
                i += 1
                continue

            state = self._goto[0].get(char, self._fail_state)
            match_end = i
            matched_action = None
            matched_positions = []

            # Follow transitions
            j = i + 1
            while state != self._fail_state and j < len(text):
                char_next = text[j].lower()
                if char_next in self._goto[state]:
                    state = self._goto[state][char_next]
                    match_end = j
                    if self._output[state] is not None:
                        matched_action = self._output[state]
                    j += 1
                else:
                    break

            # Check if we matched anything
            if matched_action is not None:
                flagged.extend([text[k] for k in range(i, match_end + 1)])

                action_priority = {"warn": 1, "replace": 2, "block": 3}.get(matched_action, 0)
                if action_priority > highest_action_priority:
                    highest_action_priority = action_priority
                    # Replace matched characters
                    for k in range(i, match_end + 1):
                        result_text[k] = "*"

            i += 1

        flagged_unique = list(set("".join(flagged)))
        action_map = {3: "block", 2: "replace", 1: "warn", 0: "pass"}
        final_action = action_map.get(highest_action_priority, "pass")

        return ModerationResult(
            passed=final_action != "block",
            action=final_action,
            original_text=text,
            moderated_text="".join(result_text) if final_action in ("replace", "pass") else None,
            flagged_words=flagged_unique,
        )


# Default empty filter for when no words are configured
_default_filter: DFAFilter | None = None


def get_filter() -> DFAFilter:
    """Get or create the default DFA filter instance."""
    global _default_filter
    if _default_filter is None:
        _default_filter = DFAFilter([])
    return _default_filter


def reload_filter(word_list: list[tuple[str, str]]) -> DFAFilter:
    """Reload the default filter with new word list."""
    global _default_filter
    _default_filter = DFAFilter(word_list)
    return _default_filter
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd backend && .venv/Scripts/python.exe -m pytest tests/core/test_moderation.py -v
# Expected: PASS
```

- [ ] **Step 5: Commit**

```bash
git add backend/core/moderation.py backend/tests/core/test_moderation.py
git commit -m "feat: P2 DFA sensitive word filter - block/replace/warn actions"
```

---

### Task 3: Blog Services & Business Logic

**Files:**
- Create: `backend/apps/blogs/services.py`
- Test: `backend/tests/apps/blogs/test_services.py`

- [ ] **Step 1: Write failing test for blog service**

```python
# backend/tests/apps/blogs/test_services.py
import pytest
from apps.blogs.services import BlogService
from apps.blogs.schemas import BlogCreate


class TestBlogService:
    async def test_create_blog(self, db_session):
        service = BlogService(db_session)
        blog_data = BlogCreate(
            title="Test Blog",
            content="This is test content",
        )
        blog = await service.create_blog(blog_data, author_id="test-author-id")
        assert blog.title == "Test Blog"
        assert blog.author_id == "test-author-id"

    async def test_create_blog_with_sensitive_words_blocked(self, db_session):
        service = BlogService(db_session)
        blog_data = BlogCreate(
            title="Test",
            content="This contains badword",
        )
        # This test depends on moderation being set up
        # Will fail initially, implementing service will handle it
```

- [ ] **Step 2: Create backend/apps/blogs/services.py**

```python
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from apps.blogs.models import Blog, Comment
from apps.blogs.schemas import BlogCreate, BlogUpdate
from core.moderation import DFAFilter, ModerationAction, get_filter, ModerationResult


class BlogService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.moderation_filter: DFAFilter = get_filter()

    async def create_blog(self, blog_data: BlogCreate, author_id: str) -> Blog:
        """Create a new blog post with content moderation."""
        # Check content for sensitive words
        combined_text = f"{blog_data.title} {blog_data.content}"
        moderation_result = self.moderation_filter.check(combined_text)

        if moderation_result.block:
            from core.exceptions import ContentBlocked
            raise ContentBlocked(
                f"Content contains prohibited words: {', '.join(moderation_result.flagged_words)}"
            )

        # If replace action, use moderated text
        title = blog_data.title
        content = blog_data.content
        if moderation_result.replace and moderation_result.moderated_text:
            # Split back into title/content (simplified - just prefix check)
            mod_text = moderation_result.moderated_text
            if moderation_result.moderated_text.startswith(blog_data.title):
                content = mod_text[len(blog_data.title):].strip()
            else:
                content = mod_text

        blog = Blog(
            title=title,
            content=content,
            excerpt=blog_data.excerpt,
            cover_image=blog_data.cover_image,
            author_id=author_id,
            category=blog_data.category,
            tags=blog_data.tags,
        )
        self.db.add(blog)
        await self.db.flush()
        await self.db.refresh(blog)
        return blog

    async def get_blog_by_id(self, blog_id: str) -> Optional[Blog]:
        result = await self.db.execute(
            select(Blog).where(Blog.id == blog_id, Blog.is_deleted == False)
        )
        return result.scalar_one_or_none()

    async def get_blogs(
        self,
        skip: int = 0,
        limit: int = 20,
        category: Optional[str] = None,
        status: str = "published",
    ) -> list[Blog]:
        query = select(Blog).where(Blog.is_deleted == False, Blog.status == status)
        if category:
            query = query.where(Blog.category == category)
        query = query.order_by(Blog.created_at.desc()).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_blog(self, blog_id: str, blog_data: BlogUpdate, author_id: str) -> Optional[Blog]:
        blog = await self.get_blog_by_id(blog_id)
        if not blog or blog.author_id != author_id:
            return None

        update_data = blog_data.model_dump(exclude_unset=True)

        # Check moderation if content is being updated
        if "content" in update_data or "title" in update_data:
            new_title = update_data.get("title", blog.title)
            new_content = update_data.get("content", blog.content)
            combined_text = f"{new_title} {new_content}"
            moderation_result = self.moderation_filter.check(combined_text)

            if moderation_result.block:
                from core.exceptions import ContentBlocked
                raise ContentBlocked("Updated content contains prohibited words")

            if moderation_result.replace and moderation_result.moderated_text:
                mod_text = moderation_result.moderated_text
                if mod_text.startswith(new_title):
                    update_data["content"] = mod_text[len(new_title):].strip()

        for key, value in update_data.items():
            setattr(blog, key, value)

        await self.db.flush()
        await self.db.refresh(blog)
        return blog

    async def delete_blog(self, blog_id: str, author_id: str) -> bool:
        blog = await self.get_blog_by_id(blog_id)
        if not blog or blog.author_id != author_id:
            return False
        blog.is_deleted = True
        await self.db.flush()
        return True

    async def increment_view_count(self, blog_id: str) -> None:
        blog = await self.get_blog_by_id(blog_id)
        if blog:
            blog.view_count += 1
            await self.db.flush()
```

- [ ] **Step 3: Add ContentBlocked exception to core/exceptions.py**

```python
class ContentBlocked(HTTPException):
    def __init__(self, detail: str = "Content contains prohibited words"):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)
```

- [ ] **Step 4: Run tests**

```bash
cd backend && .venv/Scripts/python.exe -m pytest tests/apps/blogs/test_services.py -v
```

- [ ] **Step 5: Commit**

```bash
git add backend/apps/blogs/services.py backend/core/exceptions.py backend/tests/apps/blogs/
git commit -m "feat: P2 blog services with DFA moderation"
```

---

### Task 4: Blog API Views

**Files:**
- Modify: `backend/apps/blogs/views.py`
- Modify: `backend/main.py`
- Test: `backend/tests/apps/blogs/test_views.py`

- [ ] **Step 1: Create backend/apps/blogs/views.py**

```python
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from core.database import get_db
from core.dependencies import get_current_user
from core.exceptions import ContentBlocked
from apps.users.models import User
from apps.blogs.models import Blog
from apps.blogs.schemas import BlogCreate, BlogUpdate, BlogOut, BlogListOut, MessageResponse
from apps.blogs.services import BlogService

router = APIRouter(prefix="/api/blogs", tags=["博客"])


@router.post("", response_model=BlogOut, status_code=status.HTTP_201_CREATED)
async def create_blog(
    blog_data: BlogCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = BlogService(db)
    try:
        blog = await service.create_blog(blog_data, author_id=current_user.id)
        return blog
    except ContentBlocked as e:
        raise e


@router.get("", response_model=list[BlogListOut])
async def list_blogs(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    category: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    service = BlogService(db)
    blogs = await service.get_blogs(skip=skip, limit=limit, category=category)
    return [
        BlogListOut(
            id=b.id,
            title=b.title,
            excerpt=b.excerpt,
            cover_image=b.cover_image,
            author_id=b.author_id,
            author_username="",  # Would need to join
            category=b.category,
            tags=b.tags,
            status=b.status,
            view_count=b.view_count,
            like_count=b.like_count,
            created_at=b.created_at,
        )
        for b in blogs
    ]


@router.get("/{blog_id}", response_model=BlogOut)
async def get_blog(
    blog_id: str,
    db: AsyncSession = Depends(get_db),
):
    service = BlogService(db)
    blog = await service.get_blog_by_id(blog_id)
    if not blog:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Blog not found")

    # Increment view count
    await service.increment_view_count(blog_id)

    return blog


@router.put("/{blog_id}", response_model=BlogOut)
async def update_blog(
    blog_id: str,
    blog_data: BlogUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = BlogService(db)
    try:
        blog = await service.update_blog(blog_id, blog_data, author_id=current_user.id)
        if not blog:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Blog not found")
        return blog
    except ContentBlocked as e:
        raise e


@router.delete("/{blog_id}", response_model=MessageResponse)
async def delete_blog(
    blog_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = BlogService(db)
    deleted = await service.delete_blog(blog_id, author_id=current_user.id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Blog not found")
    return MessageResponse(message="Blog deleted successfully")
```

- [ ] **Step 2: Register router in backend/main.py**

```python
from apps.blogs.views import router as blogs_router

# After app = FastAPI(...)
app.include_router(blogs_router)
```

- [ ] **Step 3: Create backend/tests/apps/blogs/test_views.py**

```python
import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


class TestBlogAPI:
    async def test_create_blog_unauthenticated(self, client: AsyncClient):
        response = await client.post("/api/blogs", json={
            "title": "Test",
            "content": "Test content",
        })
        assert response.status_code == 401

    async def test_create_blog(self, client: AsyncClient, faker_email):
        # Register and login first
        await client.post("/api/auth/register", json={
            "username": "bloguser",
            "email": faker_email,
            "password": "SecurePass123",
        })
        login_resp = await client.post(
            "/api/auth/login",
            data={"username": "bloguser", "password": "SecurePass123"},
        )
        token = login_resp.json()["access_token"]

        response = await client.post(
            "/api/blogs",
            json={"title": "My First Blog", "content": "Hello world"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "My First Blog"
        assert "id" in data

    async def test_list_blogs(self, client: AsyncClient):
        response = await client.get("/api/blogs")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
```

- [ ] **Step 4: Run tests**

```bash
cd backend && .venv/Scripts/python.exe -m pytest tests/apps/blogs/test_views.py -v
```

- [ ] **Step 5: Commit**

```bash
git add backend/apps/blogs/views.py backend/main.py backend/tests/apps/blogs/test_views.py
git commit -m "feat: P2 blog CRUD API endpoints"
```

---

## Frontend: Blog UI

### Task 5: Blog API Client & Store

**Files:**
- Create: `web-client/src/api/blogs.js`
- Modify: `web-client/src/stores/blogs.js`
- Test: none

- [ ] **Step 1: Create web-client/src/api/blogs.js**

```javascript
import client from './index'

export const blogApi = {
  createBlog(data) {
    return client.post('/api/blogs', data)
  },

  getBlogs(params) {
    return client.get('/api/blogs', { params })
  },

  getBlog(blogId) {
    return client.get(`/api/blogs/${blogId}`)
  },

  updateBlog(blogId, data) {
    return client.put(`/api/blogs/${blogId}`, data)
  },

  deleteBlog(blogId) {
    return client.delete(`/api/blogs/${blogId}`)
  },
}
```

- [ ] **Step 2: Create web-client/src/stores/blogs.js**

```javascript
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { blogApi } from '@/api/blogs'

export const useBlogStore = defineStore('blogs', () => {
  const blogs = ref([])
  const currentBlog = ref(null)
  const isLoading = ref(false)

  async function fetchBlogs(params = {}) {
    isLoading.value = true
    try {
      const response = await blogApi.getBlogs(params)
      blogs.value = response.data
    } finally {
      isLoading.value = false
    }
  }

  async function fetchBlog(blogId) {
    isLoading.value = true
    try {
      const response = await blogApi.getBlog(blogId)
      currentBlog.value = response.data
      return response.data
    } finally {
      isLoading.value = false
    }
  }

  async function createBlog(data) {
    const response = await blogApi.createBlog(data)
    return response.data
  }

  async function updateBlog(blogId, data) {
    const response = await blogApi.updateBlog(blogId, data)
    currentBlog.value = response.data
    return response.data
  }

  async function deleteBlog(blogId) {
    await blogApi.deleteBlog(blogId)
    blogs.value = blogs.value.filter(b => b.id !== blogId)
  }

  return {
    blogs,
    currentBlog,
    isLoading,
    fetchBlogs,
    fetchBlog,
    createBlog,
    updateBlog,
    deleteBlog,
  }
})
```

- [ ] **Step 3: Commit**

```bash
git add web-client/src/api/blogs.js web-client/src/stores/blogs.js
git commit -m "feat: P2 frontend blog API client and store"
```

---

### Task 6: Blog Editor View

**Files:**
- Create: `web-client/src/views/BlogEditor.vue`
- Test: none

- [ ] **Step 1: Create web-client/src/views/BlogEditor.vue**

```vue
<template>
  <div class="editor-page">
    <div class="editor-header">
      <button class="btn btn-ghost" @click="$router.back()">取消</button>
      <h2>{{ isEdit ? '编辑博客' : '写博客' }}</h2>
      <button class="btn btn-primary" @click="handleSubmit" :disabled="loading">
        {{ loading ? '发布中...' : '发布' }}
      </button>
    </div>

    <div class="editor-content">
      <input
        v-model="form.title"
        type="text"
        class="title-input"
        placeholder="文章标题"
        maxlength="200"
      >

      <textarea
        v-model="form.content"
        class="content-textarea"
        placeholder="写下你的想法..."
      ></textarea>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useBlogStore } from '@/stores/blogs'

const router = useRouter()
const route = useRoute()
const blogStore = useBlogStore()

const isEdit = route.name === 'BlogEdit'
const loading = ref(false)
const blogId = route.params.id

const form = reactive({
  title: '',
  content: '',
  excerpt: '',
  category: '',
  tags: '',
})

onMounted(async () => {
  if (isEdit && blogId) {
    const blog = await blogStore.fetchBlog(blogId)
    form.title = blog.title
    form.content = blog.content
    form.excerpt = blog.excerpt || ''
    form.category = blog.category || ''
    form.tags = blog.tags || ''
  }
})

async function handleSubmit() {
  if (!form.title.trim()) {
    ElMessage.warning('请输入标题')
    return
  }
  if (!form.content.trim()) {
    ElMessage.warning('请输入内容')
    return
  }

  loading.value = true
  try {
    if (isEdit) {
      await blogStore.updateBlog(blogId, form)
      ElMessage.success('更新成功')
    } else {
      await blogStore.createBlog(form)
      ElMessage.success('发布成功')
    }
    router.push('/blogs')
  } catch (error) {
    // Error handled by interceptor
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.editor-page {
  min-height: 100vh;
  background: #F2F9F4;
}

.editor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  background: #FFFFFF;
  border-bottom: 1px solid #DDEEE5;
}

.editor-header h2 {
  font-size: 18px;
  font-weight: 600;
}

.editor-content {
  max-width: 800px;
  margin: 0 auto;
  padding: 32px 24px;
}

.title-input {
  width: 100%;
  padding: 16px 0;
  border: none;
  font-size: 32px;
  font-family: 'Lora', 'Noto Serif SC', Georgia, serif;
  font-weight: 600;
  color: #2D3B30;
  background: transparent;
  outline: none;
}

.title-input::placeholder {
  color: #97C9A8;
}

.content-textarea {
  width: 100%;
  min-height: 400px;
  padding: 16px 0;
  border: none;
  font-size: 16px;
  line-height: 1.8;
  color: #2D3B30;
  background: transparent;
  outline: none;
  resize: vertical;
}

.content-textarea::placeholder {
  color: #97C9A8;
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 8px 16px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  border: none;
  transition: all 150ms ease;
}

.btn-primary {
  background: linear-gradient(135deg, #5A9672 0%, #7BAF8E 100%);
  color: #FFFFFF;
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-1px);
}

.btn-primary:disabled {
  opacity: 0.6;
}

.btn-ghost {
  background: transparent;
  color: #5A9672;
  border: 1px solid #C8DCD2;
}

.btn-ghost:hover {
  background: #E8F5ED;
}
</style>
```

- [ ] **Step 2: Commit**

```bash
git add web-client/src/views/BlogEditor.vue
git commit -m "feat: P2 blog editor view"
```

---

### Task 7: Blog List & Detail Views

**Files:**
- Modify: `web-client/src/views/BlogList.vue`
- Create: `web-client/src/views/BlogDetail.vue`
- Modify: `web-client/src/router/index.js`

- [ ] **Step 1: Modify web-client/src/views/BlogList.vue**

```vue
<template>
  <div class="blog-list-page">
    <div class="blog-hero">
      <h1>探索智慧的宁静角落</h1>
      <p>在这里，每一次阅读都是一次与心灵的对话。</p>
    </div>

    <main class="blog-content">
      <div class="blog-layout">
        <div class="blog-cards">
          <article
            v-for="blog in blogStore.blogs"
            :key="blog.id"
            class="blog-card"
            @click="$router.push(`/blogs/${blog.id}`)"
          >
            <div class="blog-card-cover-placeholder" v-if="!blog.cover_image">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <rect x="3" y="3" width="18" height="18" rx="2"/>
                <circle cx="8.5" cy="8.5" r="1.5"/>
                <path d="M21 15l-5-5L5 21"/>
              </svg>
            </div>
            <div class="blog-card-body">
              <div class="blog-card-meta">
                <span class="blog-card-tag" v-if="blog.category">{{ blog.category }}</span>
                <span class="blog-card-date">{{ formatDate(blog.created_at) }}</span>
              </div>
              <h2 class="blog-card-title">{{ blog.title }}</h2>
              <p class="blog-card-excerpt">{{ blog.excerpt || blog.content?.substring(0, 100) }}</p>
              <div class="blog-card-footer">
                <span class="blog-card-author">{{ blog.author_username }}</span>
                <div class="blog-card-stats">
                  <span>{{ blog.view_count }} 阅读</span>
                  <span>{{ blog.like_count }} 点赞</span>
                </div>
              </div>
            </div>
          </article>
        </div>

        <aside class="blog-sidebar">
          <button class="btn btn-primary write-btn" @click="$router.push('/blogs/new')">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 5v14M5 12h14"/>
            </svg>
            写博客
          </button>
        </aside>
      </div>
    </main>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useBlogStore } from '@/stores/blogs'

const blogStore = useBlogStore()

onMounted(() => {
  blogStore.fetchBlogs()
})

function formatDate(dateStr) {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString('zh-CN')
}
</script>

<style scoped>
.blog-list-page { min-height: 100vh; background: #F2F9F4; }

.blog-hero {
  background: linear-gradient(180deg, rgba(232,245,237,0.7) 0%, #F2F9F4 100%);
  padding: 64px 24px 48px;
  text-align: center;
  border-bottom: 1px solid #DDEEE5;
}

.blog-hero h1 {
  font-size: 36px;
  font-weight: 700;
  color: #2D3B30;
  margin-bottom: 12px;
}

.blog-hero p {
  font-size: 16px;
  color: #6B7D72;
}

.blog-content { max-width: 1100px; margin: 0 auto; padding: 40px 24px 80px; }
.blog-layout { display: grid; grid-template-columns: 1fr 280px; gap: 40px; }

.blog-card {
  background: #FFFFFF;
  border-radius: 16px;
  border: 1px solid #DDEEE5;
  overflow: hidden;
  cursor: pointer;
  transition: all 250ms ease;
  margin-bottom: 20px;
}

.blog-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 32px rgba(45,59,48,0.10);
}

.blog-card-cover-placeholder {
  height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #E8F0EB 0%, rgba(151,201,168,0.4) 100%);
}

.blog-card-cover-placeholder svg { width: 48px; height: 48px; color: #97C9A8; }

.blog-card-body { padding: 24px; }
.blog-card-meta { display: flex; align-items: center; gap: 12px; margin-bottom: 12px; }
.blog-card-tag {
  padding: 3px 10px;
  background: #E8F5ED;
  color: #5A9672;
  border-radius: 100px;
  font-size: 12px;
  font-weight: 600;
}
.blog-card-date { font-size: 12px; color: #6B7D72; }
.blog-card-title {
  font-family: 'Lora', 'Noto Serif SC', Georgia, serif;
  font-size: 19px;
  font-weight: 600;
  color: #2D3B30;
  margin-bottom: 8px;
}
.blog-card-excerpt {
  font-size: 14px;
  color: #6B7D72;
  line-height: 1.7;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.blog-card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #E8F0EB;
}
.blog-card-author { font-size: 13px; font-weight: 500; color: #2D3B30; }
.blog-card-stats { display: flex; gap: 12px; font-size: 13px; color: #6B7D72; }

.blog-sidebar { position: sticky; top: 88px; }

.write-btn {
  width: 100%;
  padding: 14px 24px;
  border-radius: 12px;
  font-size: 15px;
  font-weight: 600;
  background: linear-gradient(135deg, #5A9672 0%, #7BAF8E 100%);
  color: #FFFFFF;
  box-shadow: 0 4px 12px rgba(90,150,114,0.30);
  margin-bottom: 20px;
}

.write-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(90,150,114,0.40);
}
</style>
```

- [ ] **Step 2: Create web-client/src/views/BlogDetail.vue**

```vue
<template>
  <div class="blog-detail-page">
    <div v-if="blogStore.currentBlog" class="blog-detail">
      <header class="blog-header">
        <button class="btn btn-ghost back-btn" @click="$router.back()">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M19 12H5M12 19l-7-7 7-7"/>
          </svg>
          返回
        </button>
        <div class="blog-actions" v-if="isAuthor">
          <button class="btn btn-ghost" @click="$router.push(`/blogs/${blogId}/edit`)">编辑</button>
          <button class="btn btn-ghost delete-btn" @click="handleDelete">删除</button>
        </div>
      </header>

      <article class="blog-article">
        <h1 class="blog-title">{{ blog.title }}</h1>
        <div class="blog-meta">
          <span>{{ formatDate(blog.created_at) }}</span>
          <span>{{ blog.view_count }} 阅读</span>
        </div>
        <div class="blog-content" v-html="blog.content"></div>
      </article>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useBlogStore } from '@/stores/blogs'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const route = useRoute()
const blogStore = useBlogStore()
const authStore = useAuthStore()

const blogId = route.params.id
const blog = computed(() => blogStore.currentBlog)
const isAuthor = computed(() =>
  blog.value?.author_id === authStore.user?.id
)

onMounted(() => {
  blogStore.fetchBlog(blogId)
})

async function handleDelete() {
  try {
    await ElMessageBox.confirm('确定要删除这篇博客吗？', '删除确认', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await blogStore.deleteBlog(blogId)
    ElMessage.success('删除成功')
    router.push('/blogs')
  } catch {
    // User cancelled
  }
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })
}
</script>

<style scoped>
.blog-detail-page { min-height: 100vh; background: #F2F9F4; }

.blog-detail {
  max-width: 800px;
  margin: 0 auto;
  padding: 24px;
}

.blog-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 32px;
}

.back-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border-radius: 8px;
  font-size: 14px;
  color: #5A9672;
  background: transparent;
  border: 1px solid #C8DCD2;
  cursor: pointer;
}

.back-btn:hover { background: #E8F5ED; }

.blog-actions { display: flex; gap: 8px; }

.btn-ghost {
  padding: 8px 16px;
  border-radius: 8px;
  font-size: 14px;
  color: #5A9672;
  background: transparent;
  border: 1px solid #C8DCD2;
  cursor: pointer;
}

.btn-ghost:hover { background: #E8F5ED; }

.delete-btn { color: #DC2626; border-color: #FECACA; }
.delete-btn:hover { background: #FEF2F2; }

.blog-article {
  background: #FFFFFF;
  border-radius: 24px;
  padding: 48px;
  box-shadow: 0 4px 12px rgba(45,59,48,0.08);
  border: 1px solid #DDEEE5;
}

.blog-title {
  font-family: 'Lora', 'Noto Serif SC', Georgia, serif;
  font-size: 36px;
  font-weight: 700;
  color: #2D3B30;
  margin-bottom: 16px;
  line-height: 1.3;
}

.blog-meta {
  display: flex;
  gap: 16px;
  font-size: 14px;
  color: #6B7D72;
  margin-bottom: 32px;
  padding-bottom: 24px;
  border-bottom: 1px solid #E8F0EB;
}

.blog-content {
  font-size: 16px;
  line-height: 1.8;
  color: #2D3B30;
  white-space: pre-wrap;
}
</style>
```

- [ ] **Step 3: Update router**

```javascript
{
  path: '/blogs/new',
  name: 'BlogCreate',
  component: () => import('@/views/BlogEditor.vue'),
  meta: { requiresAuth: true },
},
{
  path: '/blogs/:id/edit',
  name: 'BlogEdit',
  component: () => import('@/views/BlogEditor.vue'),
  meta: { requiresAuth: true },
},
```

Also update the beforeEach guard to handle `requiresAuth` meta:

```javascript
if (to.meta.requiresAuth && !authStore.isLoggedIn) {
  next('/login')
}
```

- [ ] **Step 4: Commit**

```bash
git add web-client/src/views/BlogList.vue web-client/src/views/BlogDetail.vue web-client/src/router/index.js
git commit -m "feat: P2 blog list and detail views"
```

---

## Self-Review Checklist

- [ ] **Spec coverage:** All blog CRUD (create, read, update, delete) has tasks. DFA moderation (block/replace/warn) has tasks.
- [ ] **Placeholder scan:** No "TBD", "TODO", or vague steps found.
- [ ] **Type consistency:** BlogOut, BlogCreate, BlogUpdate schemas match across backend and frontend. DFA ModerationResult fields are consistent.
- [ ] **Security:** Blog update/delete requires author_id check. Unauthenticated users cannot create blogs.
- [ ] **DFA algorithm:** O(n) text scanning, longest-match priority, three action levels.
- [ ] **No placeholder code:** Every step shows actual implementation code.
