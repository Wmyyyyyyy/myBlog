from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from typing import Optional

from apps.blogs.models import Blog
from apps.comments.models import Comment
from apps.users.models import User
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
            mod_text = moderation_result.moderated_text
            if mod_text.startswith(blog_data.title):
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

        # Record dynamic event
        from apps.dynamics.services import DynamicService
        dynamic_service = DynamicService(self.db)
        await dynamic_service.record_blog_post(blog)

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
    ) -> list[tuple[Blog, str]]:
        """Returns list of (Blog, author_username) tuples."""
        query = (
            select(Blog, User.username)
            .join(User, Blog.author_id == User.id)
            .where(Blog.is_deleted == False, Blog.status == status)
        )
        if category:
            query = query.where(Blog.category == category)
        query = query.order_by(Blog.created_at.desc()).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.all())

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
