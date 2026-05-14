from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import timedelta, datetime

from core.database import get_db
from apps.admin.security import create_access_token, decode_token, ACCESS_TOKEN_EXPIRE_MINUTES
from apps.admin.schemas import (
    AdminLogin, AdminToken, AdminUserInfo,
    DashboardStats, UserGrowthItem, BlogGrowthItem, DailyActiveItem, InteractionStatsItem,
    UserItem, UserListItem, BanUserRequest, UnbanUserRequest, UpdateUserRequest, ResetPasswordRequest, ResetPasswordResponse,
    SensitiveWordItem, CreateSensitiveWord, UpdateSensitiveWord,
    WarnedBlogItem, WarnedCommentItem, ReviewAction,
    AdminLogItem,
    LoginLogItem, IPBanItem, IPBanCreate,
    BlogItem, BlogListItem, UpdateBlogRequest,
    CommentItem, CommentListItem, UpdateCommentRequest,
    SecurityLogItem, OperationLogItem,
    MessageResponse,
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


@router.get("/dashboard/online-users")
async def get_online_users(
    current_admin: User = Depends(get_current_admin),
):
    """Get count of currently online users via WebSocket connections"""
    from apps.websocket.manager import manager
    count = await manager.get_online_count()
    return {"online_count": count}


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


@router.get("/users/{user_id}", response_model=UserItem)
async def get_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """Get user detail by ID"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    from apps.blogs.models import Blog
    from apps.comments.models import Comment
    from sqlalchemy import func

    blog_count_result = await db.execute(
        select(func.count()).select_from(Blog).where(Blog.author_id == user.id)
    )
    comment_count_result = await db.execute(
        select(func.count()).select_from(Comment).where(Comment.author_id == user.id)
    )

    return UserItem(
        id=user.id,
        username=user.username,
        email=getattr(user, 'email', None),
        is_active=user.is_active,
        is_admin=user.is_admin,
        is_banned=not user.is_active,
        created_at=user.created_at,
        blog_count=blog_count_result.scalar() or 0,
        comment_count=comment_count_result.scalar() or 0,
    )


@router.put("/users/{user_id}")
async def update_user(
    user_id: str,
    data: UpdateUserRequest,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """Update user information"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if data.email is not None:
        user.email = data.email
    if data.is_active is not None:
        user.is_active = data.is_active
    if data.is_admin is not None:
        user.is_admin = data.is_admin

    await db.flush()
    return {"message": "User updated"}


@router.post("/users/{user_id}/reset-password", response_model=ResetPasswordResponse)
async def reset_user_password(
    user_id: str,
    data: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """Reset user password (admin action)"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    from apps.admin.security import get_password_hash
    import secrets

    if data.new_password:
        new_password = data.new_password
    else:
        new_password = secrets.token_urlsafe(12)

    user.password_hash = get_password_hash(new_password)
    await db.flush()

    return ResetPasswordResponse(
        message="Password reset successfully",
        new_password=new_password,
    )


@router.post("/users/{user_id}/ban")
async def ban_user_by_id(
    user_id: str,
    data: BanUserRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """Ban user by ID"""
    service = AdminUserService()
    ip = request.client.host if request.client else None
    success = await service.ban_user(db, current_admin.id, user_id, data.reason, ip)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User banned"}


@router.post("/users/{user_id}/unban")
async def unban_user_by_id(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """Unban user by ID"""
    service = AdminUserService()
    success = await service.unban_user(db, current_admin.id, user_id)
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


# ==================== Blog Management ====================

@router.get("/blogs", response_model=list[BlogListItem])
async def list_blogs(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: str = None,
    status: str = None,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """List all blogs with optional filters"""
    from apps.blogs.models import Blog
    from sqlalchemy import func, or_

    query = select(Blog)
    if search:
        query = query.where(Blog.title.ilike(f"%{search}%"))
    if status:
        query = query.where(Blog.status == status)

    query = query.offset(skip).limit(limit).order_by(Blog.created_at.desc())
    result = await db.execute(query)
    blogs = result.scalars().all()

    blog_list = []
    for blog in blogs:
        author_result = await db.execute(select(User).where(User.id == blog.author_id))
        author = author_result.scalar_one_or_none()

        from apps.interactions.models import Like
        like_count_result = await db.execute(
            select(func.count()).select_from(Like).where(Like.blog_id == blog.id)
        )
        from apps.comments.models import Comment
        comment_count_result = await db.execute(
            select(func.count()).select_from(Comment).where(Comment.blog_id == blog.id)
        )

        blog_list.append(BlogListItem(
            id=blog.id,
            title=blog.title,
            author_id=blog.author_id,
            author_username=author.username if author else "Unknown",
            status=blog.status,
            created_at=blog.created_at,
            comment_count=comment_count_result.scalar() or 0,
            like_count=like_count_result.scalar() or 0,
        ))
    return blog_list


@router.get("/blogs/{blog_id}", response_model=BlogItem)
async def get_blog(
    blog_id: str,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """Get blog detail by ID"""
    from apps.blogs.models import Blog
    from apps.interactions.models import Like
    from apps.comments.models import Comment
    from sqlalchemy import func

    result = await db.execute(select(Blog).where(Blog.id == blog_id))
    blog = result.scalar_one_or_none()
    if not blog:
        raise HTTPException(status_code=404, detail="Blog not found")

    author_result = await db.execute(select(User).where(User.id == blog.author_id))
    author = author_result.scalar_one_or_none()

    like_count_result = await db.execute(
        select(func.count()).select_from(Like).where(Like.blog_id == blog.id)
    )
    comment_count_result = await db.execute(
        select(func.count()).select_from(Comment).where(Comment.blog_id == blog.id)
    )

    return BlogItem(
        id=blog.id,
        title=blog.title,
        content=getattr(blog, 'content', ''),
        author_id=blog.author_id,
        author_username=author.username if author else "Unknown",
        status=blog.status,
        is_sensitive=getattr(blog, 'is_sensitive', False),
        created_at=blog.created_at,
        updated_at=getattr(blog, 'updated_at', None),
        comment_count=comment_count_result.scalar() or 0,
        like_count=like_count_result.scalar() or 0,
    )


@router.put("/blogs/{blog_id}")
async def update_blog(
    blog_id: str,
    data: UpdateBlogRequest,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """Update blog content"""
    from apps.blogs.models import Blog

    result = await db.execute(select(Blog).where(Blog.id == blog_id))
    blog = result.scalar_one_or_none()
    if not blog:
        raise HTTPException(status_code=404, detail="Blog not found")

    if data.title is not None:
        blog.title = data.title
    if data.content is not None:
        blog.content = data.content
    if data.status is not None:
        blog.status = data.status

    await db.flush()
    return {"message": "Blog updated"}


@router.delete("/blogs/{blog_id}")
async def delete_blog(
    blog_id: str,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """Delete a blog"""
    from apps.blogs.models import Blog

    result = await db.execute(select(Blog).where(Blog.id == blog_id))
    blog = result.scalar_one_or_none()
    if not blog:
        raise HTTPException(status_code=404, detail="Blog not found")

    await db.delete(blog)
    await db.flush()
    return {"message": "Blog deleted"}


@router.post("/blogs/{blog_id}/unmark-sensitive")
async def unmark_blog_sensitive(
    blog_id: str,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """Unmark blog as sensitive"""
    from apps.blogs.models import Blog

    result = await db.execute(select(Blog).where(Blog.id == blog_id))
    blog = result.scalar_one_or_none()
    if not blog:
        raise HTTPException(status_code=404, detail="Blog not found")

    blog.is_sensitive = False
    blog.status = "published"
    await db.flush()
    return {"message": "Blog unmark sensitive"}


# ==================== Comment Management ====================

@router.get("/comments", response_model=list[CommentListItem])
async def list_comments(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: str = None,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """List all comments with optional search"""
    from apps.comments.models import Comment
    from apps.blogs.models import Blog
    from sqlalchemy import or_

    query = select(Comment)
    if search:
        query = query.where(Comment.content.ilike(f"%{search}%"))

    query = query.offset(skip).limit(limit).order_by(Comment.created_at.desc())
    result = await db.execute(query)
    comments = result.scalars().all()

    comment_list = []
    for comment in comments:
        author_result = await db.execute(select(User).where(User.id == comment.author_id))
        author = author_result.scalar_one_or_none()

        blog_result = await db.execute(select(Blog).where(Blog.id == comment.blog_id))
        blog = blog_result.scalar_one_or_none()

        comment_list.append(CommentListItem(
            id=comment.id,
            content=comment.content,
            author_id=comment.author_id,
            author_username=author.username if author else "Unknown",
            blog_id=comment.blog_id,
            blog_title=blog.title if blog else "Unknown",
            created_at=comment.created_at,
        ))
    return comment_list


@router.get("/comments/{comment_id}", response_model=CommentItem)
async def get_comment(
    comment_id: str,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """Get comment detail by ID"""
    from apps.comments.models import Comment
    from apps.blogs.models import Blog

    result = await db.execute(select(Comment).where(Comment.id == comment_id))
    comment = result.scalar_one_or_none()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    author_result = await db.execute(select(User).where(User.id == comment.author_id))
    author = author_result.scalar_one_or_none()

    blog_result = await db.execute(select(Blog).where(Blog.id == comment.blog_id))
    blog = blog_result.scalar_one_or_none()

    return CommentItem(
        id=comment.id,
        content=comment.content,
        author_id=comment.author_id,
        author_username=author.username if author else "Unknown",
        blog_id=comment.blog_id,
        blog_title=blog.title if blog else "Unknown",
        is_sensitive=getattr(comment, 'is_sensitive', False),
        created_at=comment.created_at,
    )


@router.put("/comments/{comment_id}")
async def update_comment(
    comment_id: str,
    data: UpdateCommentRequest,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """Update comment content"""
    from apps.comments.models import Comment

    result = await db.execute(select(Comment).where(Comment.id == comment_id))
    comment = result.scalar_one_or_none()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    if data.content is not None:
        comment.content = data.content

    await db.flush()
    return {"message": "Comment updated"}


@router.delete("/comments/{comment_id}")
async def delete_comment(
    comment_id: str,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """Delete a comment"""
    from apps.comments.models import Comment

    result = await db.execute(select(Comment).where(Comment.id == comment_id))
    comment = result.scalar_one_or_none()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    await db.delete(comment)
    await db.flush()
    return {"message": "Comment deleted"}


@router.post("/comments/{comment_id}/unmark-sensitive")
async def unmark_comment_sensitive(
    comment_id: str,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """Unmark comment as sensitive"""
    from apps.comments.models import Comment

    result = await db.execute(select(Comment).where(Comment.id == comment_id))
    comment = result.scalar_one_or_none()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    comment.is_sensitive = False
    await db.flush()
    return {"message": "Comment unmark sensitive"}


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


# ==================== Logs ====================

@router.get("/logs/security", response_model=list[SecurityLogItem])
async def list_security_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    ip_address: str = None,
    user_id: str = None,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """List security logs"""
    from apps.admin.models import SecurityLog
    from sqlalchemy import select, and_

    query = select(SecurityLog)
    conditions = []
    if ip_address:
        conditions.append(SecurityLog.ip == ip_address)
    if user_id:
        conditions.append(SecurityLog.user_id == user_id)

    if conditions:
        query = query.where(and_(*conditions))

    query = query.order_by(SecurityLog.timestamp.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    logs = result.scalars().all()

    return [
        SecurityLogItem(
            id=log.id,
            ip=log.ip,
            timestamp=log.timestamp,
            endpoint=log.endpoint,
            method=log.method,
            result=log.result,
            triggered_rule=log.triggered_rule,
            action_taken=log.action_taken,
            user_id=log.user_id,
            request_params=log.request_params,
        )
        for log in logs
    ]


@router.get("/logs/security/export")
async def export_security_logs(
    ip_address: str = None,
    user_id: str = None,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """Export security logs as CSV"""
    from apps.admin.models import SecurityLog
    from sqlalchemy import select, and_
    import csv
    from fastapi.responses import StreamingResponse
    from io import StringIO

    query = select(SecurityLog)
    conditions = []
    if ip_address:
        conditions.append(SecurityLog.ip == ip_address)
    if user_id:
        conditions.append(SecurityLog.user_id == user_id)

    if conditions:
        query = query.where(and_(*conditions))

    query = query.order_by(SecurityLog.timestamp.desc()).limit(1000)
    result = await db.execute(query)
    logs = result.scalars().all()

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "IP", "Timestamp", "Endpoint", "Method", "Result", "Triggered Rule", "Action Taken", "User ID"])

    for log in logs:
        writer.writerow([
            log.id, log.ip, log.timestamp, log.endpoint, log.method,
            log.result, log.triggered_rule, log.action_taken, log.user_id
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=security_logs.csv"}
    )


@router.get("/logs/operation", response_model=list[OperationLogItem])
async def list_operation_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    admin_id: str = None,
    action: str = None,
    target_type: str = None,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """List operation logs"""
    from apps.admin.models import AdminOperationLog
    from sqlalchemy import select, and_

    query = select(AdminOperationLog)
    conditions = []
    if admin_id:
        conditions.append(AdminOperationLog.admin_id == admin_id)
    if action:
        conditions.append(AdminOperationLog.action.like(f"%{action}%"))
    if target_type:
        conditions.append(AdminOperationLog.target_type == target_type)

    if conditions:
        query = query.where(and_(*conditions))

    query = query.order_by(AdminOperationLog.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    logs = result.scalars().all()

    return [
        OperationLogItem(
            id=log.id,
            admin_id=log.admin_id,
            action=log.action,
            target_type=log.target_type,
            target_id=log.target_id,
            detail=log.detail,
            ip=log.ip,
            created_at=log.created_at,
        )
        for log in logs
    ]


@router.get("/logs/login", response_model=list[LoginLogItem])
async def list_login_logs_direct(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    ip_address: str = None,
    status: str = None,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """List login logs (alternative path)"""
    service = AdminSecurityService()
    return await service.list_login_logs(db, skip, limit, ip_address, status)


# ==================== IP Bans (Direct Paths) ====================

@router.get("/ip-bans", response_model=list[IPBanItem])
async def list_ip_bans_direct(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    active_only: bool = True,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """List IP bans (alternative path)"""
    service = AdminSecurityService()
    bans = await service.list_bans(db, skip, limit, active_only)
    return [
        IPBanItem(
            id=ban["id"],
            ip_address=ban["ip_address"],
            reason=ban["reason"],
            banned_by=ban["banned_by"],
            banned_at=ban["banned_at"],
            expires_at=ban["expires_at"],
            is_active=ban["is_active"],
        )
        for ban in bans
    ]


@router.post("/ip-bans", status_code=status.HTTP_201_CREATED)
async def create_ip_ban_direct(
    data: IPBanCreate,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """Create IP ban (alternative path)"""
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


@router.delete("/ip-bans/{ip_address}")
async def delete_ip_ban_direct(
    ip_address: str,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """Delete/unban IP (alternative path)"""
    service = AdminSecurityService()
    success = await service.unban_ip(db, ip_address)
    if not success:
        raise HTTPException(status_code=404, detail="IP not found in ban list")
    return {"message": "IP unbanned"}


@router.post("/ip-bans/{ip_address}/unban-all")
async def unban_all_ips(
    ip_address: str,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """Unban all IPs (remove all bans for an IP)"""
    service = AdminSecurityService()
    success = await service.unban_ip(db, ip_address)
    if not success:
        raise HTTPException(status_code=404, detail="IP not found in ban list")
    return {"message": "All bans for IP removed"}
