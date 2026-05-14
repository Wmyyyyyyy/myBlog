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