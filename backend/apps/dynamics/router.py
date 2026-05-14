from urllib.parse import unquote
import json
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.dependencies import get_current_user
from apps.users.models import User
from apps.dynamics.services import DynamicService
from apps.dynamics.schemas import FeedResponse

router = APIRouter(prefix="/api/dynamics", tags=["动态"])


def parse_cursor(cursor_str: str) -> dict:
    if not cursor_str:
        return None
    return json.loads(unquote(cursor_str))


@router.get("/feed", response_model=FeedResponse)
async def get_my_feed(
    cursor: str = Query(None, description="分页游标，URL编码的JSON"),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取当前用户的动态流（关注的人的最新动态）"""
    service = DynamicService(db)
    parsed_cursor = parse_cursor(cursor) if cursor else None
    return await service.get_user_feed(current_user.id, parsed_cursor, limit)


@router.get("/user/{user_id}", response_model=FeedResponse)
async def get_user_events(
    user_id: str,
    cursor: str = Query(None, description="分页游标，URL编码的JSON"),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """获取某个用户的事件列表"""
    service = DynamicService(db)
    parsed_cursor = parse_cursor(cursor) if cursor else None
    return await service.get_user_events(user_id, parsed_cursor, limit)