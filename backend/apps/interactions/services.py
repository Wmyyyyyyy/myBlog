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