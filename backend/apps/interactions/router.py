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

    # Record dynamic event
    from apps.dynamics.services import DynamicService
    from apps.blogs.models import Blog
    from sqlalchemy import select
    blog_result = await db.execute(select(Blog).where(Blog.id == blog_id))
    blog = blog_result.scalar_one_or_none()
    if blog:
        dynamic_service = DynamicService(db)
        await dynamic_service.record_like_blog(current_user.id, blog_id, blog.author_id)

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

        # Record dynamic event
        from apps.dynamics.services import DynamicService
        dynamic_service = DynamicService(db)
        await dynamic_service.record_follow(current_user.id, user_id)

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