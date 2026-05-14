from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.dependencies import get_current_user
from apps.users.models import User
from apps.foundation.schemas import CheckInResponse, CheckInStatus, CheckInHistory, MessageResponse
from apps.foundation.services import FoundationService

router = APIRouter(prefix="/api/foundation", tags=["百日筑基"])


@router.post("/checkin", response_model=CheckInResponse, status_code=status.HTTP_201_CREATED)
async def checkin(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = FoundationService(db)
    try:
        result = await service.checkin(user_id=current_user.id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/status", response_model=CheckInStatus)
async def get_status(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = FoundationService(db)
    result = await service.get_checkin_status(user_id=current_user.id)
    return result


@router.get("/history", response_model=CheckInHistory)
async def get_history(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = FoundationService(db)
    records, total = await service.get_checkin_history(
        user_id=current_user.id,
        skip=skip,
        limit=limit
    )
    return {
        "records": [
            {"check_in_date": r.check_in_date, "created_at": r.created_at}
            for r in records
        ],
        "total": total
    }
