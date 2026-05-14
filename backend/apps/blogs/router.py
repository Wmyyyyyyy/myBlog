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

router = APIRouter(prefix="/api/blogs", tags=["blogs"])


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
            author_username=author_username,
            category=b.category,
            tags=b.tags,
            status=b.status,
            view_count=b.view_count,
            like_count=b.like_count,
            created_at=b.created_at,
        )
        for b, author_username in blogs
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


@router.post("/{blog_id}/view", status_code=status.HTTP_204_NO_CONTENT)
async def increment_view(
    blog_id: str,
    db: AsyncSession = Depends(get_db),
):
    service = BlogService(db)
    blog = await service.get_blog_by_id(blog_id)
    if not blog:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Blog not found")
    await service.increment_view_count(blog_id)