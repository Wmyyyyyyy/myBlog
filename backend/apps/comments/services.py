from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from apps.comments.models import Comment
from apps.users.models import User
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
            select(Comment).where(Comment.id == comment_id, Comment.comment_status != 0)
        )
        return result.scalar_one_or_none()

    async def get_comments_by_blog(
        self,
        blog_id: str,
        skip: int = 0,
        limit: int = 20,
        sort: str = "latest",  # "latest" or "hottest"
    ) -> list[tuple[Comment, str]]:
        """获取博客的所有一级评论，返回(comment, author_username)元组列表"""
        query = (
            select(Comment, User.username)
            .join(User, Comment.author_id == User.id)
            .where(
                Comment.blog_id == blog_id,
                Comment.parent_id.is_(None),  # 只查一级评论
                Comment.comment_status != 0
            )
        )

        if sort == "hottest":
            query = query.order_by(Comment.like_count.desc(), Comment.created_at.desc())
        else:
            query = query.order_by(Comment.created_at.desc())

        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.all())

    async def get_replies(
        self,
        root_id: str,
        skip: int = 0,
        limit: int = 10,
    ) -> list[tuple[Comment, str]]:
        """获取某个根评论下的所有回复，返回(comment, author_username)元组列表"""
        query = (
            select(Comment, User.username)
            .join(User, Comment.author_id == User.id)
            .where(
                Comment.root_id == root_id,
                Comment.comment_status != 0
            )
            .order_by(Comment.created_at.asc())
        )

        result = await self.db.execute(query)
        return list(result.all())

    async def delete_comment(self, comment_id: str, author_id: str) -> bool:
        """软删除评论"""
        comment = await self.get_comment_by_id(comment_id)
        if not comment or comment.author_id != author_id:
            return False
        comment.comment_status = 0
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
