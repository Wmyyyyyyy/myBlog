import uuid as uuid_lib
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
        return CommentOut(
            id=comment.id,
            blog_id=comment.blog_id,
            author_id=comment.author_id,
            author_username=current_user.username,
            content=comment.content,
            parent_id=comment.parent_id,
            root_id=comment.root_id,
            level=comment.level,
            like_count=comment.like_count,
            reply_count=comment.reply_count,
            comment_status=comment.comment_status,
            created_at=comment.created_at,
            updated_at=comment.updated_at,
        )
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
    try:
        uuid_lib.UUID(blog_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid blog ID format")

    service = CommentService(db)
    comments = await service.get_comments_by_blog(blog_id, skip, limit, sort)
    return [
        CommentOut(
            id=c.id,
            blog_id=c.blog_id,
            author_id=c.author_id,
            author_username=author_username,
            content=c.content,
            parent_id=c.parent_id,
            root_id=c.root_id,
            level=c.level,
            like_count=c.like_count,
            reply_count=c.reply_count,
            comment_status=c.comment_status,
            created_at=c.created_at,
            updated_at=c.updated_at,
        )
        for c, author_username in comments
    ]


@router.get("/{comment_id}/replies", response_model=list[CommentOut])
async def get_comment_replies(
    comment_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    try:
        uuid_lib.UUID(comment_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid comment ID format")

    service = CommentService(db)
    replies = await service.get_replies(comment_id, skip, limit)
    return [
        CommentOut(
            id=c.id,
            blog_id=c.blog_id,
            author_id=c.author_id,
            author_username=author_username,
            content=c.content,
            parent_id=c.parent_id,
            root_id=c.root_id,
            level=c.level,
            like_count=c.like_count,
            reply_count=c.reply_count,
            comment_status=c.comment_status,
            created_at=c.created_at,
            updated_at=c.updated_at,
        )
        for c, author_username in replies
    ]


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
