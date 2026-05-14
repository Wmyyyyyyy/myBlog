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