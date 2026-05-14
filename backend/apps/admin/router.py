from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import timedelta, datetime

from core.database import get_db
from apps.admin.security import create_access_token, decode_token, ACCESS_TOKEN_EXPIRE_MINUTES
from apps.admin.schemas import (
    AdminLogin, AdminToken, AdminUserInfo,
    DashboardStats, UserGrowthItem, BlogGrowthItem, DailyActiveItem, InteractionStatsItem,
    UserItem, BanUserRequest, UnbanUserRequest,
    SensitiveWordItem, CreateSensitiveWord, UpdateSensitiveWord,
    WarnedBlogItem, WarnedCommentItem, ReviewAction,
    AdminLogItem,
    LoginLogItem, IPBanItem, CreateIPBan,
)
from apps.admin.services import (
    AdminAuthService, AdminDashboardService, AdminUserService,
    AdminSensitiveWordService, AdminReviewService, AdminLogService,
    AdminSecurityService,
)
from apps.users.models import User

router = APIRouter(prefix="/api/admin", tags=["Admin"])


async def get_current_admin(request: Request, db: AsyncSession = Depends(get_db)) -> User:
    """验证管理员 token"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = auth_header.split(" ")[1]
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    result = await db.execute(select(User).where(User.id == user_id, User.is_admin == True))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="Not an admin")

    return user


# ==================== Auth ====================

@router.post("/login", response_model=AdminToken)
async def admin_login(
    login_data: AdminLogin,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")

    security_service = AdminSecurityService()

    is_banned, ban_reason, ban_expires = await security_service.is_ip_banned(db, client_ip)
    if is_banned:
        await security_service.record_login(db, client_ip, user_agent, "failed", fail_reason=f"IP被封禁: {ban_reason}")
        raise HTTPException(status_code=403, detail=f"IP已被封禁: {ban_reason}")

    service = AdminAuthService(db)
    user = await service.authenticate(login_data.username, login_data.password)

    if not user:
        await security_service.record_login(db, client_ip, user_agent, "failed", fail_reason="Invalid credentials")
        raise HTTPException(status_code=401, detail="Invalid credentials")

    await security_service.record_login(db, client_ip, user_agent, "success", admin_id=user.id)

    access_token = create_access_token(
        data={"sub": user.id, "username": user.username},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return AdminToken(access_token=access_token)


@router.get("/me", response_model=AdminUserInfo)
async def get_admin_me(current_admin: User = Depends(get_current_admin)):
    return AdminUserInfo(
        id=current_admin.id,
        username=current_admin.username,
        email=getattr(current_admin, 'email', None),
    )


# ==================== Dashboard ====================

@router.get("/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    service = AdminDashboardService()
    return await service.get_stats(db)


@router.get("/dashboard/user-growth", response_model=list[UserGrowthItem])
async def get_user_growth(
    days: int = Query(30, ge=7, le=90),
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    service = AdminDashboardService()
    return await service.get_user_growth(db, days)


@router.get("/dashboard/blog-growth", response_model=list[BlogGrowthItem])
async def get_blog_growth(
    days: int = Query(30, ge=7, le=90),
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    service = AdminDashboardService()
    return await service.get_blog_growth(db, days)


@router.get("/dashboard/dau", response_model=list[DailyActiveItem])
async def get_dau_stats(
    days: int = Query(30, ge=7, le=90),
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    service = AdminDashboardService()
    return await service.get_dau_stats(db, days)


@router.get("/dashboard/interactions", response_model=list[InteractionStatsItem])
async def get_interaction_stats(
    days: int = Query(30, ge=7, le=90),
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    service = AdminDashboardService()
    return await service.get_interaction_stats(db, days)


# ==================== User Management ====================

@router.get("/users", response_model=list[UserItem])
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: str = None,
    is_active: bool = None,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    service = AdminUserService()
    return await service.list_users(db, skip, limit, search, is_active)


@router.post("/users/ban")
async def ban_user(
    data: BanUserRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    service = AdminUserService()
    ip = request.client.host if request.client else None
    success = await service.ban_user(db, current_admin.id, data.user_id, data.reason, ip)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User banned"}


@router.post("/users/unban")
async def unban_user(
    data: UnbanUserRequest,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    service = AdminUserService()
    success = await service.unban_user(db, current_admin.id, data.user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User unbanned"}


# ==================== Sensitive Words ====================

@router.get("/sensitive-words", response_model=list[SensitiveWordItem])
async def list_sensitive_words(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    service = AdminSensitiveWordService(db)
    return await service.list_words(skip, limit)


@router.post("/sensitive-words", status_code=status.HTTP_201_CREATED)
async def create_sensitive_word(
    data: CreateSensitiveWord,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    service = AdminSensitiveWordService(db)
    result = await service.add_word(current_admin.id, data.word, data.action)
    return result


@router.put("/sensitive-words/{word_id}")
async def update_sensitive_word(
    word_id: str,
    data: UpdateSensitiveWord,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    service = AdminSensitiveWordService(db)
    success = await service.update_word(current_admin.id, word_id, data.word, data.action)
    if not success:
        raise HTTPException(status_code=404, detail="Word not found")
    return {"message": "Word updated"}


@router.delete("/sensitive-words/{word_id}")
async def delete_sensitive_word(
    word_id: str,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    service = AdminSensitiveWordService(db)
    success = await service.delete_word(current_admin.id, word_id)
    if not success:
        raise HTTPException(status_code=404, detail="Word not found")
    return {"message": "Word deleted"}


@router.post("/sensitive-words/reload")
async def reload_sensitive_words(
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    service = AdminSensitiveWordService(db)
    await service.reload_filter()
    return {"message": "Filter reloaded"}


# ==================== Content Review ====================

@router.get("/review/blogs", response_model=list[WarnedBlogItem])
async def get_warned_blogs(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    service = AdminReviewService()
    return await service.get_warned_blogs(db, skip, limit)


@router.get("/review/comments", response_model=list[WarnedCommentItem])
async def get_warned_comments(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    service = AdminReviewService()
    return await service.get_warned_comments(db, skip, limit)


@router.post("/review/blogs/{blog_id}")
async def review_blog(
    blog_id: str,
    data: ReviewAction,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    service = AdminReviewService()
    success = await service.review_blog(db, current_admin.id, blog_id, data.action, data.reason)
    return {"message": f"Blog {data.action}d"}


@router.post("/review/comments/{comment_id}")
async def review_comment(
    comment_id: str,
    data: ReviewAction,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    service = AdminReviewService()
    success = await service.review_comment(db, current_admin.id, comment_id, data.action, data.reason)
    return {"message": f"Comment {data.action}d"}


# ==================== Admin Logs ====================

@router.get("/logs", response_model=list[AdminLogItem])
async def list_admin_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    admin_id: str = None,
    action: str = None,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    service = AdminLogService()
    return await service.list_logs(db, skip, limit, admin_id, action)


# ==================== Security: Login Logs ====================

@router.get("/security/login-logs", response_model=list[LoginLogItem])
async def list_login_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    ip_address: str = None,
    status: str = None,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    service = AdminSecurityService()
    return await service.list_login_logs(db, skip, limit, ip_address, status)


# ==================== Security: IP Bans ====================

@router.get("/security/ip-bans", response_model=list[IPBanItem])
async def list_ip_bans(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    active_only: bool = True,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    service = AdminSecurityService()
    return await service.list_bans(db, skip, limit, active_only)


@router.post("/security/ip-bans", status_code=status.HTTP_201_CREATED)
async def create_ip_ban(
    data: CreateIPBan,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    service = AdminSecurityService()
    expires_at = None
    if data.expires_in_minutes:
        expires_at = datetime.now() + timedelta(minutes=data.expires_in_minutes)

    ban = await service.ban_ip(
        db,
        ip_address=data.ip_address,
        reason=data.reason or "手动封禁",
        banned_by=current_admin.username,
        expires_at=expires_at,
    )
    return {
        "id": ban.id,
        "ip_address": ban.ip_address,
        "reason": ban.reason,
        "banned_by": ban.banned_by,
        "banned_at": ban.banned_at,
        "expires_at": ban.expires_at,
    }


@router.delete("/security/ip-bans/{ip_address}")
async def delete_ip_ban(
    ip_address: str,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    service = AdminSecurityService()
    success = await service.unban_ip(db, ip_address)
    if not success:
        raise HTTPException(status_code=404, detail="IP not found in ban list")
    return {"message": "IP unbanned"}
