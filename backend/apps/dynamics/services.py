import json
from datetime import datetime, timedelta
from sqlalchemy import select, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession

from apps.dynamics.models import DynamicEvent
from apps.dynamics.schemas import DynamicEventOut, FeedResponse
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
        target_title: str = None,
    ) -> DynamicEvent:
        """创建动态事件"""
        event = DynamicEvent(
            user_id=user_id,
            event_type=event_type,
            target_id=target_id,
            target_user_id=target_user_id,
            target_title=target_title,
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
            target_title=blog.title[:100] if blog.title else None,
        )

    async def record_like_blog(self, user_id: str, blog_id: str, blog_author_id: str) -> DynamicEvent:
        """记录点赞博客事件"""
        return await self.create_event(
            user_id=user_id,
            event_type="like_blog",
            target_id=blog_id,
            target_user_id=blog_author_id,
        )

    async def record_favorite_blog(self, user_id: str, blog_id: str, blog_author_id: str) -> DynamicEvent:
        """记录收藏博客事件"""
        return await self.create_event(
            user_id=user_id,
            event_type="favorite_blog",
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

    async def record_checkin(self, user_id: str, achievement_id: str, achievement_name: str) -> DynamicEvent:
        """记录签到/筑基事件"""
        return await self.create_event(
            user_id=user_id,
            event_type="checkin",
            target_id=achievement_id,
            target_title=achievement_name,
        )

    async def get_user_feed(
        self,
        user_id: str,
        cursor: dict = None,
        limit: int = 20,
    ) -> FeedResponse:
        """
        获取用户的动态流（拉模式）：
        1. 获取用户关注的人
        2. 聚合这些人的最新事件
        3. 按时间排序
        使用游标分页，返回30天内的动态
        """
        from apps.interactions.models import Follow

        # 查询关注的人
        result = await self.db.execute(
            select(Follow.following_id).where(Follow.follower_id == user_id)
        )
        following_ids = [row[0] for row in result.fetchall()]

        # 加入自己（显示自己的博客）
        user_ids = following_ids + [user_id]

        if not user_ids:
            return FeedResponse(events=[], next_cursor=None)

        # 基础查询：30天内的动态
        query = select(DynamicEvent).where(
            DynamicEvent.user_id.in_(user_ids),
            DynamicEvent.created_at >= datetime.now() - timedelta(days=30)
        )

        # 游标分页
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

        query = query.order_by(
            DynamicEvent.created_at.desc(),
            DynamicEvent.id.desc()
        ).limit(limit + 1)  # 多查一条判断是否有下一页

        result = await self.db.execute(query)
        events = list(result.scalars().all())

        # 判断是否有下一页
        has_more = len(events) > limit
        if has_more:
            events = events[:limit]

        # 构建下一页游标
        next_cursor = None
        if has_more and events:
            last_event = events[-1]
            next_cursor = {
                "created_at": last_event.created_at.isoformat(),
                "id": last_event.id
            }

        # 补充用户信息和博客信息
        enriched_events = []
        for event in events:
            event_dict = await self._enrich_event(event)
            enriched_events.append(event_dict)

        return FeedResponse(events=enriched_events, next_cursor=next_cursor)

    async def _enrich_event(self, event: DynamicEvent) -> dict:
        """补充事件的关联信息"""
        event_dict = {
            "id": event.id,
            "user_id": event.user_id,
            "event_type": event.event_type,
            "target_id": event.target_id,
            "target_title": event.target_title,
            "target_user_id": event.target_user_id,
            "created_at": event.created_at,
        }

        # 补充用户信息
        user_result = await self.db.execute(
            select(User).where(User.id == event.user_id)
        )
        user = user_result.scalar_one_or_none()
        if user:
            event_dict["user_username"] = user.username
            event_dict["user_avatar"] = getattr(user, 'avatar', None)

        # 补充目标用户信息
        if event.target_user_id:
            target_user_result = await self.db.execute(
                select(User).where(User.id == event.target_user_id)
            )
            target_user = target_user_result.scalar_one_or_none()
            if target_user:
                event_dict["target_user_username"] = target_user.username

        # 补充博客信息（如果是 blog_post、like_blog 或 favorite_blog）
        if event.target_id and event.event_type in ("blog_post", "like_blog", "favorite_blog"):
            blog_result = await self.db.execute(
                select(Blog).where(Blog.id == event.target_id)
            )
            blog = blog_result.scalar_one_or_none()
            if blog:
                event_dict["blog_title"] = blog.title
                event_dict["blog_cover"] = blog.cover_image

        return event_dict

    async def get_user_events(
        self,
        user_id: str,
        cursor: dict = None,
        limit: int = 20,
    ) -> FeedResponse:
        """获取某个用户的所有事件（使用游标分页）"""
        # 基础查询
        query = select(DynamicEvent).where(DynamicEvent.user_id == user_id)

        # 游标分页
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

        query = query.order_by(
            DynamicEvent.created_at.desc(),
            DynamicEvent.id.desc()
        ).limit(limit + 1)

        result = await self.db.execute(query)
        events = list(result.scalars().all())

        # 判断是否有下一页
        has_more = len(events) > limit
        if has_more:
            events = events[:limit]

        # 构建下一页游标
        next_cursor = None
        if has_more and events:
            last_event = events[-1]
            next_cursor = {
                "created_at": last_event.created_at.isoformat(),
                "id": last_event.id
            }

        # 补充事件信息
        enriched_events = []
        for event in events:
            event_dict = await self._enrich_event(event)
            enriched_events.append(event_dict)

        return FeedResponse(events=enriched_events, next_cursor=next_cursor)