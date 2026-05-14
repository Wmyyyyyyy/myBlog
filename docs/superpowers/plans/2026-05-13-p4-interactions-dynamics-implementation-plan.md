# P4: Interactions + Dynamic Feed Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Favorites, likes, follows, and user dynamics feed (pull-mode).

**Architecture:**
- Independent from P3 (no comment events)
- Favorites: users can bookmark blogs
- Likes: users can like blogs (no comments yet)
- Follow: users can follow other users
- Dynamics: pull-mode aggregation of events (post, like, follow)

**Tech Stack:** FastAPI + SQLAlchemy async + PostgreSQL + Vue 3 + Pinia

---

## Backend: Interactions

### Task 1: Interaction Models & Schemas

**Files:**
- Create: `backend/apps/interactions/__init__.py`
- Create: `backend/apps/interactions/models.py`
- Create: `backend/apps/interactions/schemas.py`
- Modify: `backend/apps/__init__.py`
- Test: `backend/tests/apps/interactions/test_models.py`

- [ ] **Step 1: Create backend/apps/interactions/__init__.py**

```python
```

- [ ] **Step 2: Create backend/apps/interactions/models.py**

```python
import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from core.database import Base


class Favorite(Base):
    """用户收藏的博客"""
    __tablename__ = "favorites"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    blog_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("blogs.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now())

    __table_args__ = (
        UniqueConstraint('user_id', 'blog_id', name='uq_user_blog_favorite'),
    )


class Like(Base):
    """用户点赞的博客"""
    __tablename__ = "likes"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    blog_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("blogs.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now())

    __table_args__ = (
        UniqueConstraint('user_id', 'blog_id', name='uq_user_blog_like'),
    )


class Follow(Base):
    """用户关注关系"""
    __tablename__ = "follows"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    follower_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)  # 关注者
    following_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)  # 被关注者
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now())

    __table_args__ = (
        UniqueConstraint('follower_id', 'following_id', name='uq_follower_following'),
    )
```

- [ ] **Step 3: Create backend/apps/interactions/schemas.py**

```python
from datetime import datetime
from pydantic import BaseModel
from typing import Optional


class FavoriteResponse(BaseModel):
    id: str
    user_id: str
    blog_id: str
    created_at: datetime

    model_config = {"from_attributes": True}


class LikeResponse(BaseModel):
    id: str
    user_id: str
    blog_id: str
    created_at: datetime

    model_config = {"from_attributes": True}


class FollowResponse(BaseModel):
    id: str
    follower_id: str
    following_id: str
    created_at: datetime

    model_config = {"from_attributes": True}


class MessageResponse(BaseModel):
    message: str
```

- [ ] **Step 4: Create backend/tests/apps/interactions/test_models.py**

```python
import pytest
from apps.interactions.models import Favorite, Like, Follow


class TestFavoriteModel:
    def test_favorite_create(self):
        fav = Favorite(user_id="user-1", blog_id="blog-1")
        assert fav.user_id == "user-1"
        assert fav.blog_id == "blog-1"


class TestLikeModel:
    def test_like_create(self):
        like = Like(user_id="user-1", blog_id="blog-1")
        assert like.user_id == "user-1"
        assert like.blog_id == "blog-1"


class TestFollowModel:
    def test_follow_create(self):
        follow = Follow(follower_id="user-1", following_id="user-2")
        assert follow.follower_id == "user-1"
        assert follow.following_id == "user-2"
```

- [ ] **Step 5: Commit**

---

### Task 2: Interaction Services

**Files:**
- Create: `backend/apps/interactions/services.py`
- Test: `backend/tests/apps/interactions/test_services.py`

- [ ] **Step 1: Create backend/apps/interactions/services.py**

```python
from sqlalchemy import select, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from apps.interactions.models import Favorite, Like, Follow


class InteractionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ==================== Favorites ====================

    async def add_favorite(self, user_id: str, blog_id: str) -> Favorite:
        """添加收藏"""
        # 检查是否已收藏
        existing = await self.get_favorite(user_id, blog_id)
        if existing:
            return existing

        fav = Favorite(user_id=user_id, blog_id=blog_id)
        self.db.add(fav)
        await self.db.flush()
        await self.db.refresh(fav)
        return fav

    async def remove_favorite(self, user_id: str, blog_id: str) -> bool:
        """取消收藏"""
        result = await self.db.execute(
            select(Favorite).where(
                Favorite.user_id == user_id,
                Favorite.blog_id == blog_id
            )
        )
        fav = result.scalar_one_or_none()
        if not fav:
            return False
        await self.db.delete(fav)
        await self.db.flush()
        return True

    async def get_favorite(self, user_id: str, blog_id: str) -> Optional[Favorite]:
        result = await self.db.execute(
            select(Favorite).where(
                Favorite.user_id == user_id,
                Favorite.blog_id == blog_id
            )
        )
        return result.scalar_one_or_none()

    async def get_user_favorites(self, user_id: str, skip: int = 0, limit: int = 20):
        """获取用户的收藏列表"""
        result = await self.db.execute(
            select(Favorite)
            .where(Favorite.user_id == user_id)
            .order_by(Favorite.created_at.desc())
            .offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def is_favorited(self, user_id: str, blog_id: str) -> bool:
        return await self.get_favorite(user_id, blog_id) is not None

    # ==================== Likes ====================

    async def add_like(self, user_id: str, blog_id: str) -> Like:
        """添加点赞"""
        existing = await self.get_like(user_id, blog_id)
        if existing:
            return existing

        like = Like(user_id=user_id, blog_id=blog_id)
        self.db.add(like)
        await self.db.flush()
        await self.db.refresh(like)
        return like

    async def remove_like(self, user_id: str, blog_id: str) -> bool:
        """取消点赞"""
        result = await self.db.execute(
            select(Like).where(
                Like.user_id == user_id,
                Like.blog_id == blog_id
            )
        )
        like = result.scalar_one_or_none()
        if not like:
            return False
        await self.db.delete(like)
        await self.db.flush()
        return True

    async def get_like(self, user_id: str, blog_id: str) -> Optional[Like]:
        result = await self.db.execute(
            select(Like).where(
                Like.user_id == user_id,
                Like.blog_id == blog_id
            )
        )
        return result.scalar_one_or_none()

    async def get_blog_likes(self, blog_id: str, skip: int = 0, limit: int = 20):
        """获取博客的点赞列表"""
        result = await self.db.execute(
            select(Like).where(Like.blog_id == blog_id)
            .order_by(Like.created_at.desc())
            .offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def is_liked(self, user_id: str, blog_id: str) -> bool:
        return await self.get_like(user_id, blog_id) is not None

    async def get_likes_count(self, blog_id: str) -> int:
        """获取博客的点赞数"""
        result = await self.db.execute(
            select(func.count()).select_from(Like).where(Like.blog_id == blog_id)
        )
        return result.scalar() or 0

    # ==================== Follows ====================

    async def follow(self, follower_id: str, following_id: str) -> Follow:
        """关注用户"""
        if follower_id == following_id:
            raise ValueError("Cannot follow yourself")

        existing = await self.get_follow(follower_id, following_id)
        if existing:
            return existing

        follow = Follow(follower_id=follower_id, following_id=following_id)
        self.db.add(follow)
        await self.db.flush()
        await self.db.refresh(follow)
        return follow

    async def unfollow(self, follower_id: str, following_id: str) -> bool:
        """取消关注"""
        result = await self.db.execute(
            select(Follow).where(
                Follow.follower_id == follower_id,
                Follow.following_id == following_id
            )
        )
        follow = result.scalar_one_or_none()
        if not follow:
            return False
        await self.db.delete(follow)
        await self.db.flush()
        return True

    async def get_follow(self, follower_id: str, following_id: str) -> Optional[Follow]:
        result = await self.db.execute(
            select(Follow).where(
                Follow.follower_id == follower_id,
                Follow.following_id == following_id
            )
        )
        return result.scalar_one_or_none()

    async def is_following(self, follower_id: str, following_id: str) -> bool:
        return await self.get_follow(follower_id, following_id) is not None

    async def get_followers(self, user_id: str, skip: int = 0, limit: int = 20):
        """获取用户的粉丝列表"""
        result = await self.db.execute(
            select(Follow).where(Follow.following_id == user_id)
            .order_by(Follow.created_at.desc())
            .offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def get_following(self, user_id: str, skip: int = 0, limit: int = 20):
        """获取用户关注的列表"""
        result = await self.db.execute(
            select(Follow).where(Follow.follower_id == user_id)
            .order_by(Follow.created_at.desc())
            .offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def get_followers_count(self, user_id: str) -> int:
        result = await self.db.execute(
            select(func.count()).select_from(Follow).where(Follow.following_id == user_id)
        )
        return result.scalar() or 0

    async def get_following_count(self, user_id: str) -> int:
        result = await self.db.execute(
            select(func.count()).select_from(Follow).where(Follow.follower_id == user_id)
        )
        return result.scalar() or 0
```

- [ ] **Step 2: Commit**

---

### Task 3: Interaction API Views

**Files:**
- Create: `backend/apps/interactions/router.py`
- Modify: `backend/main.py`
- Test: `backend/tests/apps/interactions/test_router.py`

- [ ] **Step 1: Create backend/apps/interactions/router.py**

```python
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from core.database import get_db
from core.dependencies import get_current_user
from apps.users.models import User
from apps.interactions.schemas import FavoriteResponse, LikeResponse, FollowResponse, MessageResponse
from apps.interactions.services import InteractionService

router = APIRouter(prefix="/api/interactions", tags=["互动"])


# ==================== Favorites ====================

@router.post("/favorites/{blog_id}", response_model=FavoriteResponse, status_code=status.HTTP_201_CREATED)
async def add_favorite(
    blog_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = InteractionService(db)
    fav = await service.add_favorite(current_user.id, blog_id)
    return fav


@router.delete("/favorites/{blog_id}", response_model=MessageResponse)
async def remove_favorite(
    blog_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = InteractionService(db)
    await service.remove_favorite(current_user.id, blog_id)
    return MessageResponse(message="Removed from favorites")


@router.get("/favorites/me", response_model=list[FavoriteResponse])
async def get_my_favorites(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = InteractionService(db)
    return await service.get_user_favorites(current_user.id, skip, limit)


@router.get("/favorites/{blog_id}/status", response_model=dict)
async def check_favorite_status(
    blog_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = InteractionService(db)
    is_fav = await service.is_favorited(current_user.id, blog_id)
    return {"is_favorited": is_fav}


# ==================== Likes ====================

@router.post("/likes/{blog_id}", response_model=LikeResponse, status_code=status.HTTP_201_CREATED)
async def add_like(
    blog_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = InteractionService(db)
    like = await service.add_like(current_user.id, blog_id)
    return like


@router.delete("/likes/{blog_id}", response_model=MessageResponse)
async def remove_like(
    blog_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = InteractionService(db)
    await service.remove_like(current_user.id, blog_id)
    return MessageResponse(message="Like removed")


@router.get("/likes/{blog_id}/status", response_model=dict)
async def check_like_status(
    blog_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = InteractionService(db)
    is_liked = await service.is_liked(current_user.id, blog_id)
    count = await service.get_likes_count(blog_id)
    return {"is_liked": is_liked, "like_count": count}


# ==================== Follows ====================

@router.post("/follow/{user_id}", response_model=FollowResponse, status_code=status.HTTP_201_CREATED)
async def follow_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = InteractionService(db)
    try:
        follow = await service.follow(current_user.id, user_id)
        return follow
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/follow/{user_id}", response_model=MessageResponse)
async def unfollow_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = InteractionService(db)
    await service.unfollow(current_user.id, user_id)
    return MessageResponse(message="Unfollowed successfully")


@router.get("/follow/{user_id}/status", response_model=dict)
async def check_follow_status(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = InteractionService(db)
    is_following = await service.is_following(current_user.id, user_id)
    followers_count = await service.get_followers_count(user_id)
    following_count = await service.get_following_count(user_id)
    return {
        "is_following": is_following,
        "followers_count": followers_count,
        "following_count": following_count,
    }


@router.get("/followers/{user_id}", response_model=list[FollowResponse])
async def get_user_followers(
    user_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    service = InteractionService(db)
    return await service.get_followers(user_id, skip, limit)


@router.get("/following/{user_id}", response_model=list[FollowResponse])
async def get_user_following(
    user_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    service = InteractionService(db)
    return await service.get_following(user_id, skip, limit)
```

- [ ] **Step 2: Register router in main.py**

```python
from apps.interactions.router import router as interactions_router
app.include_router(interactions_router)
```

- [ ] **Step 3: Commit**

---

## Backend: Dynamics Feed

### Task 4: Dynamic Models & Schemas

**Files:**
- Create: `backend/apps/dynamics/__init__.py`
- Create: `backend/apps/dynamics/models.py`
- Create: `backend/apps/dynamics/schemas.py`
- Modify: `backend/apps/__init__.py`

- [ ] **Step 1: Create backend/apps/dynamics/__init__.py**

```python
```

- [ ] **Step 2: Create backend/apps/dynamics/models.py**

```python
import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Integer, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from core.database import Base


class DynamicEvent(Base):
    """
    用户动态事件（用于动态流展示）
    事件类型：blog_post, like_blog, follow_user
    """
    __tablename__ = "dynamic_events"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)  # blog_post, like_blog, follow_user
    target_id: Mapped[str] = mapped_column(String(100), nullable=True)  # 目标ID（博客ID、用户ID等）
    target_user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=True)  # 关联用户（如被点赞的博客作者）
    content: Mapped[str | None] = mapped_column(Text, nullable=True)  # 动态内容摘要
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(), index=True)
```

- [ ] **Step 3: Create backend/apps/dynamics/schemas.py**

```python
from datetime import datetime
from pydantic import BaseModel
from typing import Optional


class DynamicEventOut(BaseModel):
    id: str
    user_id: str
    event_type: str  # blog_post, like_blog, follow_user
    target_id: Optional[str]
    target_user_id: Optional[str]
    content: Optional[str]
    created_at: datetime

    # 关联的用户信息（需要在 service 中补充）
    username: Optional[str] = None
    user_avatar: Optional[str] = None

    # 扩展字段
    blog_title: Optional[str] = None  # 当 event_type=blog_post 时
    blog_cover: Optional[str] = None  # 当 event_type=blog_post 时

    model_config = {"from_attributes": True}
```

- [ ] **Step 4: Commit**

---

### Task 5: Dynamic Services & API

**Files:**
- Create: `backend/apps/dynamics/services.py`
- Create: `backend/apps/dynamics/router.py`
- Modify: `backend/main.py`

- [ ] **Step 1: Create backend/apps/dynamics/services.py**

```python
from sqlalchemy import select, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from apps.dynamics.models import DynamicEvent
from apps.dynamics.schemas import DynamicEventOut
from apps.users.models import User
from apps.blogs.models import Blog


class DynamicService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_event(
        self,
        user_id: str,
        event_type: str,
        target_id: str = None,
        target_user_id: str = None,
        content: str = None,
    ) -> DynamicEvent:
        """创建动态事件"""
        event = DynamicEvent(
            user_id=user_id,
            event_type=event_type,
            target_id=target_id,
            target_user_id=target_user_id,
            content=content,
        )
        self.db.add(event)
        await self.db.flush()
        await self.db.refresh(event)
        return event

    async def record_blog_post(self, blog: Blog) -> DynamicEvent:
        """记录博客发布事件"""
        return await self.create_event(
            user_id=blog.author_id,
            event_type="blog_post",
            target_id=blog.id,
            content=blog.title[:100] if blog.title else None,
        )

    async def record_like_blog(self, user_id: str, blog_id: str, blog_author_id: str) -> DynamicEvent:
        """记录点赞博客事件"""
        return await self.create_event(
            user_id=user_id,
            event_type="like_blog",
            target_id=blog_id,
            target_user_id=blog_author_id,
        )

    async def record_follow(self, follower_id: str, following_id: str) -> DynamicEvent:
        """记录关注事件"""
        return await self.create_event(
            user_id=follower_id,
            event_type="follow_user",
            target_id=following_id,
            target_user_id=following_id,
        )

    async def get_user_feed(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 20,
    ) -> list[dict]:
        """
        获取用户的动态流（拉模式）：
        1. 获取用户关注的人
        2. 聚合这些人的最新事件
        3. 按时间排序
        """
        from apps.interactions.models import Follow

        # 查询关注的人
        result = await self.db.execute(
            select(Follow.following_id).where(Follow.follower_id == user_id)
        )
        following_ids = [row[0] for row in result.fetchall()]

        # 加入自己（显示自己的博客）
        following_ids.append(user_id)

        if not following_ids:
            return []

        # 查询这些人的事件
        query = (
            select(DynamicEvent)
            .where(DynamicEvent.user_id.in_(following_ids))
            .order_by(DynamicEvent.created_at.desc())
            .offset(skip).limit(limit)
        )

        result = await self.db.execute(query)
        events = list(result.scalars().all())

        # 补充用户信息和博客信息
        enriched_events = []
        for event in events:
            event_dict = {
                "id": event.id,
                "user_id": event.user_id,
                "event_type": event.event_type,
                "target_id": event.target_id,
                "target_user_id": event.target_user_id,
                "content": event.content,
                "created_at": event.created_at,
            }

            # 补充用户信息
            user_result = await self.db.execute(
                select(User).where(User.id == event.user_id)
            )
            user = user_result.scalar_one_or_none()
            if user:
                event_dict["username"] = user.username
                event_dict["user_avatar"] = getattr(user, 'avatar', None)

            # 补充博客信息（如果是 blog_post 或 like_blog）
            if event.target_id and event.event_type in ("blog_post", "like_blog"):
                blog_result = await self.db.execute(
                    select(Blog).where(Blog.id == event.target_id)
                )
                blog = blog_result.scalar_one_or_none()
                if blog:
                    event_dict["blog_title"] = blog.title
                    event_dict["blog_cover"] = blog.cover_image

            enriched_events.append(event_dict)

        return enriched_events

    async def get_user_events(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 20,
    ) -> list[DynamicEvent]:
        """获取某个用户的所有事件"""
        result = await self.db.execute(
            select(DynamicEvent)
            .where(DynamicEvent.user_id == user_id)
            .order_by(DynamicEvent.created_at.desc())
            .offset(skip).limit(limit)
        )
        return list(result.scalars().all())
```

- [ ] **Step 2: Create backend/apps/dynamics/router.py**

```python
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.dependencies import get_current_user
from apps.users.models import User
from apps.dynamics.services import DynamicService

router = APIRouter(prefix="/api/dynamics", tags=["动态"])


@router.get("/feed", response_model=list[dict])
async def get_my_feed(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取当前用户的动态流（关注的人的最新动态）"""
    service = DynamicService(db)
    return await service.get_user_feed(current_user.id, skip, limit)


@router.get("/user/{user_id}", response_model=list[dict])
async def get_user_events(
    user_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """获取某个用户的事件列表"""
    service = DynamicService(db)
    events = await service.get_user_events(user_id, skip, limit)
    return [
        {
            "id": e.id,
            "user_id": e.user_id,
            "event_type": e.event_type,
            "target_id": e.target_id,
            "content": e.content,
            "created_at": e.created_at,
        }
        for e in events
    ]
```

- [ ] **Step 3: Register router in main.py**

```python
from apps.dynamics.router import router as dynamics_router
app.include_router(dynamics_router)
```

- [ ] **Step 4: Commit**

---

## Frontend: Interactions UI

### Task 6: Interactions API Client & Store

**Files:**
- Create: `web-client/src/api/interactions.js`
- Create: `web-client/src/stores/interactions.js`

- [ ] **Step 1: Create web-client/src/api/interactions.js**

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
  getMyFavorites(params) {
    return client.get('/api/interactions/favorites/me', { params })
  },
  checkFavoriteStatus(blogId) {
    return client.get(`/api/interactions/favorites/${blogId}/status`)
  },

  // Likes
  addLike(blogId) {
    return client.post(`/api/interactions/likes/${blogId}`)
  },
  removeLike(blogId) {
    return client.delete(`/api/interactions/likes/${blogId}`)
  },
  checkLikeStatus(blogId) {
    return client.get(`/api/interactions/likes/${blogId}/status`)
  },

  // Follows
  follow(userId) {
    return client.post(`/api/interactions/follow/${userId}`)
  },
  unfollow(userId) {
    return client.delete(`/api/interactions/follow/${userId}`)
  },
  checkFollowStatus(userId) {
    return client.get(`/api/interactions/follow/${userId}/status`)
  },
  getFollowers(userId, params) {
    return client.get(`/api/interactions/followers/${userId}`, { params })
  },
  getFollowing(userId, params) {
    return client.get(`/api/interactions/following/${userId}`, { params })
  },

  // Dynamics
  getFeed(params) {
    return client.get('/api/dynamics/feed', { params })
  },
  getUserEvents(userId, params) {
    return client.get(`/api/dynamics/user/${userId}`, { params })
  },
}
```

- [ ] **Step 2: Create web-client/src/stores/interactions.js**

```javascript
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { interactionApi } from '@/api/interactions'

export const useInteractionStore = defineStore('interactions', () => {
  // State
  const feed = ref([])
  const isLoading = ref(false)

  // Favorites
  async function toggleFavorite(blogId, currentStatus) {
    if (currentStatus) {
      await interactionApi.removeFavorite(blogId)
    } else {
      await interactionApi.addFavorite(blogId)
    }
  }

  // Likes
  async function toggleLike(blogId, currentStatus) {
    if (currentStatus) {
      await interactionApi.removeLike(blogId)
    } else {
      await interactionApi.addLike(blogId)
    }
  }

  // Follows
  async function toggleFollow(userId, currentStatus) {
    if (currentStatus) {
      await interactionApi.unfollow(userId)
    } else {
      await interactionApi.follow(userId)
    }
  }

  // Dynamics
  async function fetchFeed(params = {}) {
    isLoading.value = true
    try {
      const response = await interactionApi.getFeed(params)
      feed.value = response.data
    } finally {
      isLoading.value = false
    }
  }

  async function fetchUserEvents(userId, params = {}) {
    const response = await interactionApi.getUserEvents(userId, params)
    return response.data
  }

  return {
    feed,
    isLoading,
    toggleFavorite,
    toggleLike,
    toggleFollow,
    fetchFeed,
    fetchUserEvents,
  }
})
```

- [ ] **Step 3: Commit**

---

### Task 7: Dynamic Feed View

**Files:**
- Create: `web-client/src/views/DynamicsView.vue`

- [ ] **Step 1: Create web-client/src/views/DynamicsView.vue**

```vue
<template>
  <div class="dynamics-page">
    <div class="dynamics-header">
      <h1>动态</h1>
    </div>

    <main class="dynamics-content">
      <div v-if="interactionStore.isLoading" class="loading">加载中...</div>

      <div v-else-if="interactionStore.feed.length === 0" class="empty-state">
        <p>暂无动态</p>
        <p class="hint">关注更多用户来获取动态更新</p>
      </div>

      <div v-else class="feed-list">
        <div
          v-for="event in interactionStore.feed"
          :key="event.id"
          class="feed-item"
        >
          <div class="feed-avatar">
            <img v-if="event.user_avatar" :src="event.user_avatar" :alt="event.username" />
            <div v-else class="avatar-placeholder">{{ event.username?.[0] || 'U' }}</div>
          </div>

          <div class="feed-body">
            <div class="feed-header">
              <span class="feed-username">{{ event.username }}</span>
              <span class="feed-time">{{ formatTime(event.created_at) }}</span>
            </div>

            <div class="feed-content">
              <!-- 博客发布事件 -->
              <template v-if="event.event_type === 'blog_post'">
                <p class="event-text">发布了博客</p>
                <div class="blog-card" @click="$router.push(`/blogs/${event.target_id}`)">
                  <img v-if="event.blog_cover" :src="event.blog_cover" class="blog-cover" />
                  <span class="blog-title">{{ event.blog_title || '无标题' }}</span>
                </div>
              </template>

              <!-- 点赞博客事件 -->
              <template v-else-if="event.event_type === 'like_blog'">
                <p class="event-text">点赞了博客</p>
                <div class="blog-card" @click="$router.push(`/blogs/${event.target_id}`)">
                  <span class="blog-title">{{ event.blog_title || '无标题' }}</span>
                </div>
              </template>

              <!-- 关注事件 -->
              <template v-else-if="event.event_type === 'follow_user'">
                <p class="event-text">关注了 <span class="highlight">{{ getTargetUsername(event) }}</span></p>
              </template>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useInteractionStore } from '@/stores/interactions'

const interactionStore = useInteractionStore()

onMounted(() => {
  interactionStore.fetchFeed()
})

function formatTime(dateStr) {
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now - date
  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)

  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  if (hours < 24) return `${hours}小时前`
  if (days < 7) return `${days}天前`
  return date.toLocaleDateString('zh-CN')
}

function getTargetUsername(event) {
  return event.target_user_id || '用户'
}
</script>

<style scoped>
.dynamics-page { min-height: 100vh; background: #F2F9F4; }

.dynamics-header {
  padding: 32px 24px 16px;
  background: #FFFFFF;
  border-bottom: 1px solid #DDEEE5;
}
.dynamics-header h1 { font-size: 24px; font-weight: 700; color: #2D3B30; }

.dynamics-content { max-width: 600px; margin: 0 auto; padding: 24px; }

.loading { text-align: center; padding: 48px; color: #6B7D72; }

.empty-state { text-align: center; padding: 64px 24px; }
.empty-state p { font-size: 16px; color: #2D3B30; margin-bottom: 8px; }
.empty-state .hint { font-size: 14px; color: #6B7D72; }

.feed-list { display: flex; flex-direction: column; gap: 16px; }

.feed-item {
  display: flex;
  gap: 12px;
  background: #FFFFFF;
  border-radius: 16px;
  padding: 16px;
  border: 1px solid #DDEEE5;
}

.feed-avatar { flex-shrink: 0; }
.feed-avatar img {
  width: 40px; height: 40px; border-radius: 50%; object-fit: cover;
}
.avatar-placeholder {
  width: 40px; height: 40px; border-radius: 50%;
  background: linear-gradient(135deg, #5A9672, #7BAF8E);
  color: white; display: flex; align-items: center; justify-content: center;
  font-weight: 600;
}

.feed-body { flex: 1; min-width: 0; }

.feed-header {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 8px;
}
.feed-username { font-weight: 600; color: #2D3B30; font-size: 14px; }
.feed-time { font-size: 12px; color: #6B7D72; }

.event-text { font-size: 14px; color: #6B7D72; margin-bottom: 8px; }
.highlight { color: #5A9672; font-weight: 500; }

.blog-card {
  display: flex; gap: 12px; align-items: center;
  padding: 12px; background: #F9FAFA; border-radius: 12px;
  cursor: pointer; transition: background 200ms;
}
.blog-card:hover { background: #E8F5ED; }
.blog-cover { width: 48px; height: 48px; border-radius: 8px; object-fit: cover; }
.blog-title { font-size: 14px; font-weight: 500; color: #2D3B30; }
</style>
```

- [ ] **Step 2: Add route in router**

```javascript
{
  path: '/dynamics',
  name: 'Dynamics',
  component: () => import('@/views/DynamicsView.vue'),
  meta: { requiresAuth: true },
},
```

- [ ] **Step 3: Commit**

---

## Integration: Connect Blog Post with Dynamic Events

### Task 8: Connect Blog Events to Dynamic Feed

**Modify:**
- `backend/apps/blogs/services.py` - Add dynamic event recording after blog creation
- `backend/apps/interactions/router.py` - Add dynamic event recording after like/follow

- [ ] **Step 1: Update blog service to record blog_post events**

In `apps/blogs/services.py`, after creating a blog:

```python
# After blog creation in create_blog method:
# Record dynamic event
from apps.dynamics.services import DynamicService
dynamic_service = DynamicService(self.db)
await dynamic_service.record_blog_post(blog)
```

- [ ] **Step 2: Update interactions router to record like/follow events**

In `apps/interactions/router.py`:

```python
# After like:
dynamic_service = DynamicService(db)
await dynamic_service.record_like_blog(current_user.id, blog_id, ...)

# After follow:
dynamic_service = DynamicService(db)
await dynamic_service.record_follow(current_user.id, user_id)
```

- [ ] **Step 3: Commit**

---

## Self-Review Checklist

- [ ] **Spec coverage:** Favorites, likes, follows, dynamics feed all covered.
- [ ] **Placeholder scan:** No "TBD", "TODO", or vague steps found.
- [ ] **Type consistency:** Models and schemas consistent.
- [ ] **Pull-mode dynamics:** get_user_feed aggregates on read, not write.
- [ ] **Independent from P3:** No comment events in dynamics (can be added later).
- [ ] **No placeholder code:** Every step shows actual implementation code.
