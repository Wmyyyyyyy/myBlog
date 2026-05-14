from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.dependencies import get_current_user
from apps.users.models import User
from apps.foundation.schemas import CheckInResponse, CheckInHistory, AchievementInfo
from apps.foundation.services import FoundationService

router = APIRouter(prefix="/api/foundation", tags=["百日筑基"])


@router.post("/checkin", response_model=CheckInResponse, status_code=status.HTTP_201_CREATED)
async def check_in(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = FoundationService(db)
    try:
        checkin, new_achievements = await service.check_in(current_user.id)
        return CheckInResponse(
            id=checkin.id,
            user_id=checkin.user_id,
            check_in_date=checkin.check_in_date,
            streak=checkin.streak,
            achieved_achievements=new_achievements,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/status", response_model=dict)
async def get_status(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取今日打卡状态"""
    service = FoundationService(db)
    return await service.get_today_status(current_user.id)


@router.get("/history", response_model=CheckInHistory)
async def get_history(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取打卡历史（用于日历展示）"""
    service = FoundationService(db)
    return await service.get_checkin_history(current_user.id)


@router.get("/achievements", response_model=list[AchievementInfo])
async def get_achievements(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取成就列表"""
    service = FoundationService(db)
    return await service.get_achievements(current_user.id)
