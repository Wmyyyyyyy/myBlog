import json
from sqlalchemy import select, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from apps.interactions.models import Favorite, Like, Follow
from apps.blogs.models import Blog
from core.redis import redis_client


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

    async def get_favorites_count(self, blog_id: str) -> int:
        """获取博客的收藏数"""
        result = await self.db.execute(
            select(func.count()).select_from(Favorite).where(Favorite.blog_id == blog_id)
        )
        return result.scalar() or 0

    async def check_favorite_status(self, user_id: str, blog_id: str) -> bool:
        """检查是否已收藏"""
        return await self.is_favorited(user_id, blog_id)

    # ==================== Likes ====================

    async def add_like(self, user_id: str, blog_id: str) -> Like:
        """添加点赞"""
        existing = await self.get_like(user_id, blog_id)
        if existing:
            return existing

        # Get blog author for dynamics recording
        blog_result = await self.db.execute(
            select(Blog).where(Blog.id == blog_id)
        )
        blog = blog_result.scalar_one_or_none()

        like = Like(user_id=user_id, blog_id=blog_id)
        self.db.add(like)
        await self.db.flush()
        await self.db.refresh(like)

        # Write to dynamics
        if blog:
            from apps.dynamics.services import DynamicService
            dynamic_service = DynamicService(self.db)
            await dynamic_service.record_like_blog(
                user_id=user_id,
                blog_id=blog_id,
                blog_author_id=blog.author_id
            )

        # 发布动态事件到 Redis
        await self._publish_dynamic_event(
            event_type="like_blog",
            user_id=user_id,
            target_id=blog_id,
            data={"blog_id": blog_id}
        )

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

    async def check_like_status(self, user_id: str, blog_id: str) -> bool:
        """检查是否已点赞"""
        return await self.is_liked(user_id, blog_id)

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

        # Write to dynamics
        from apps.dynamics.services import DynamicService
        dynamic_service = DynamicService(self.db)
        await dynamic_service.record_follow(
            follower_id=follower_id,
            following_id=following_id
        )

        # 发布动态事件到 Redis
        await self._publish_dynamic_event(
            event_type="follow_user",
            user_id=follower_id,
            target_id=following_id,
            data={"target_user_id": following_id}
        )

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

    async def check_follow_status(self, follower_id: str, following_id: str) -> bool:
        """检查是否已关注"""
        return await self.is_following(follower_id, following_id)

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

    async def _publish_dynamic_event(
        self,
        event_type: str,
        user_id: str,
        target_id: str,
        data: dict
    ):
        """发布动态事件到 Redis"""
        # 获取目标用户的粉丝列表（用于推送）
        # 对于 follow 事件，target_id 是被关注者，需要获取其粉丝
        # 对于 like_blog 事件，target_id 是博客ID，需要获取博客作者的粉丝
        target_user_id = target_id

        if event_type == "follow_user":
            # follow 事件中 target_id 是被关注者的ID
            followers = await self.get_followers(target_user_id, limit=100)
            follower_ids = [f.follower_id for f in followers]
        elif event_type == "like_blog":
            # like_blog 事件中 target_id 是博客ID，需要查作者
            from apps.blogs.models import Blog
            blog_result = await self.db.execute(
                select(Blog.author_id).where(Blog.id == target_id)
            )
            blog_author_id = blog_result.scalar_one_or_none()
            if blog_author_id:
                followers = await self.get_followers(blog_author_id, limit=100)
                follower_ids = [f.follower_id for f in followers]
            else:
                follower_ids = []
        else:
            follower_ids = []

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

        try:
            await redis_client.publish("dynamic_events", json.dumps(message, default=str))
        except Exception:
            # Redis 发布失败不应影响主流程
            pass