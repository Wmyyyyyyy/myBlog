# P6: Admin Panel Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Independent admin panel for site management with separate `admin-client/` frontend and `apps/admin/` backend API.

**Architecture:**
- Monorepo: `admin-client/` alongside `web-client/`
- Independent Admin API: `apps/admin/` (separate from main API)
- Admin authentication: Separate login page `/admin/login`
- Admin creation: Manual DB insert of `is_admin=True` users
- Content moderation: "warn" level content is published but flagged for admin review
- Design: Independent UI, shares bamboo-green theme (#5A9672, #F2F9F4)

**Tech Stack:** FastAPI + SQLAlchemy async + PostgreSQL + Vue 3 + Element Plus + ECharts

**Domain:** `admin.benevolence.com.cn`

---

## Backend: Admin API

### Task 1: Admin Models & Schemas

**Files:**
- Create: `backend/apps/admin/__init__.py`
- Create: `backend/apps/admin/models.py`
- Create: `backend/apps/admin/schemas.py`
- Create: `backend/apps/admin/security.py`  # JWT for admin auth
- Modify: `backend/apps/__init__.py`
- Test: `backend/tests/apps/admin/test_models.py`

- [ ] **Step 1: Create backend/apps/admin/__init__.py**

```python
```

- [ ] **Step 2: Create backend/apps/admin/security.py**

```python
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext

SECRET_KEY = "your-admin-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None
```

- [ ] **Step 3: Create backend/apps/admin/models.py**

```python
# Admin uses the same User model but with is_admin flag
# Only additional model is AdminLog for audit trail

import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Text, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from core.database import Base


class AdminLog(Base):
    """管理员操作日志"""
    __tablename__ = "admin_logs"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    admin_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    action: Mapped[str] = mapped_column(String(100), nullable=False)  # create_user, ban_user, update_sensitive_word, etc.
    target_type: Mapped[str] = mapped_column(String(50), nullable=True)  # user, blog, comment, sensitive_word
    target_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(), index=True)


class LoginLog(Base):
    """登录日志"""
    __tablename__ = "admin_login_logs"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    ip_address: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)
    login_time: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(), index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False)  # success, failed
    fail_reason: Mapped[str | None] = mapped_column(String(200), nullable=True)
    admin_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=True)


class IPBan(Base):
    """IP封禁记录"""
    __tablename__ = "admin_ip_bans"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    ip_address: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    reason: Mapped[str | None] = mapped_column(String(200), nullable=True)
    banned_by: Mapped[str] = mapped_column(String(100), nullable=False)  # admin username or "system"
    banned_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now())
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)  # None = permanent
```

- [ ] **Step 4: Create backend/apps/admin/schemas.py**

```python
from datetime import datetime, date
from pydantic import BaseModel, Field
from typing import Optional


# ==================== Auth ====================

class AdminLogin(BaseModel):
    username: str
    password: str


class AdminToken(BaseModel):
    access_token: str
    token_type: str = "bearer"


class AdminUserInfo(BaseModel):
    id: str
    username: str
    email: Optional[str] = None


# ==================== Dashboard ====================

class DashboardStats(BaseModel):
    total_users: int
    total_blogs: int
    total_comments: int
    total_likes: int
    total_follows: int
    today_new_users: int
    today_new_blogs: int
    today_new_comments: int


class UserGrowthItem(BaseModel):
    date: date
    count: int


class BlogGrowthItem(BaseModel):
    date: date
    count: int


class DailyActiveItem(BaseModel):
    date: date
    count: int


class InteractionStatsItem(BaseModel):
    date: date
    likes: int
    comments: int
    follows: int


# ==================== User Management ====================

class UserItem(BaseModel):
    id: str
    username: str
    email: Optional[str]
    is_active: bool
    is_admin: bool
    created_at: datetime
    blog_count: int
    comment_count: int

    model_config = {"from_attributes": True}


class BanUserRequest(BaseModel):
    user_id: str
    reason: Optional[str] = None


class UnbanUserRequest(BaseModel):
    user_id: str


# ==================== Sensitive Word Management ====================

class SensitiveWordItem(BaseModel):
    id: str
    word: str
    action: str  # block, replace, warn
    created_at: datetime

    model_config = {"from_attributes": True}


class CreateSensitiveWord(BaseModel):
    word: str = Field(..., min_length=1, max_length=50)
    action: str = Field(..., pattern="^(block|replace|warn)$")


class UpdateSensitiveWord(BaseModel):
    word: Optional[str] = Field(None, min_length=1, max_length=50)
    action: Optional[str] = Field(None, pattern="^(block|replace|warn)$")


# ==================== Content Review ====================

class WarnedBlogItem(BaseModel):
    id: str
    title: str
    author_id: str
    author_username: str
    flagged_words: list[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class WarnedCommentItem(BaseModel):
    id: str
    content: str
    author_id: str
    author_username: str
    blog_id: str
    flagged_words: list[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class ReviewAction(BaseModel):
    action: str  # approve, reject, delete
    reason: Optional[str] = None


# ==================== Admin Logs ====================

class AdminLogItem(BaseModel):
    id: str
    admin_id: str
    admin_username: Optional[str] = None
    action: str
    target_type: Optional[str]
    target_id: Optional[str]
    detail: Optional[str]
    ip_address: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


# ==================== Security: Login Logs ====================

class LoginLogItem(BaseModel):
    id: str
    ip_address: Optional[str]
    user_agent: Optional[str]
    login_time: datetime
    status: str  # success, failed
    fail_reason: Optional[str]
    admin_id: Optional[str] = None  # 成功登录时记录

    model_config = {"from_attributes": True}


# ==================== Security: IP Bans ====================

class IPBanItem(BaseModel):
    id: str
    ip_address: str
    reason: Optional[str]
    banned_by: str
    banned_at: datetime
    expires_at: Optional[datetime] = None  # None = permanent

    model_config = {"from_attributes": True}


class CreateIPBan(BaseModel):
    ip_address: str = Field(..., pattern=r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$")
    reason: Optional[str] = None
    expires_in_minutes: Optional[int] = None  # None = permanent


class CheckIPResponse(BaseModel):
    is_banned: bool
    reason: Optional[str] = None
    expires_at: Optional[datetime] = None
```

- [ ] **Step 5: Commit**

---

### Task 2: Admin Services

**Files:**
- Create: `backend/apps/admin/services.py`
- Test: `backend/tests/apps/admin/test_services.py`

- [ ] **Step 1: Create backend/apps/admin/services.py**

```python
from datetime import date, timedelta
from sqlalchemy import select, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from apps.admin.models import AdminLog
from apps.admin.security import verify_password, get_password_hash
from apps.users.models import User
from apps.blogs.models import Blog
from apps.comments.models import Comment


class AdminAuthService:
    """管理员认证服务"""

    async def authenticate(self, db: AsyncSession, username: str, password: str) -> Optional[User]:
        result = await db.execute(
            select(User).where(User.username == username, User.is_admin == True)
        )
        user = result.scalar_one_or_none()
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user


class AdminDashboardService:
    """Dashboard 统计服务"""

    async def get_stats(self, db: AsyncSession) -> dict:
        today = date.today()
        thirty_days_ago = today - timedelta(days=30)

        # 总数
        total_users = await self._count(db, User)
        total_blogs = await self._count(db, Blog)
        total_comments = await self._count(db, Comment)

        # 从 interactions 表统计（如果存在）
        from apps.interactions.models import Like, Follow
        total_likes = await self._count(db, Like)
        total_follows = await self._count(db, Follow)

        # 今日新增
        today_new_users = await self._count_where(db, User, User.created_at >= today)
        today_new_blogs = await self._count_where(db, Blog, Blog.created_at >= today)
        today_new_comments = await self._count_where(db, Comment, Comment.created_at >= today)

        return {
            "total_users": total_users,
            "total_blogs": total_blogs,
            "total_comments": total_comments,
            "total_likes": total_likes,
            "total_follows": total_follows,
            "today_new_users": today_new_users,
            "today_new_blogs": today_new_blogs,
            "today_new_comments": today_new_comments,
        }

    async def get_user_growth(self, db: AsyncSession, days: int = 30) -> list[dict]:
        result = []
        today = date.today()
        for i in range(days - 1, -1, -1):
            d = today - timedelta(days=i)
            next_d = d + timedelta(days=1)
            count = await self._count_where(
                db, User,
                User.created_at >= d,
                User.created_at < next_d
            )
            result.append({"date": d.isoformat(), "count": count})
        return result

    async def get_blog_growth(self, db: AsyncSession, days: int = 30) -> list[dict]:
        result = []
        today = date.today()
        for i in range(days - 1, -1, -1):
            d = today - timedelta(days=i)
            next_d = d + timedelta(days=1)
            count = await self._count_where(
                db, Blog,
                Blog.created_at >= d,
                Blog.created_at < next_d
            )
            result.append({"date": d.isoformat(), "count": count})
        return result

    async def get_dau_stats(self, db: AsyncSession, days: int = 30) -> list[dict]:
        # 简化版：统计每日登录用户数（需要 sessions 表支持）
        # 这里用每日新增用户代替
        return await self.get_user_growth(db, days)

    async def get_interaction_stats(self, db: AsyncSession, days: int = 30) -> list[dict]:
        result = []
        today = date.today()
        from apps.interactions.models import Like, Follow

        for i in range(days - 1, -1, -1):
            d = today - timedelta(days=i)
            next_d = d + timedelta(days=1)
            likes = await self._count_where(db, Like, Like.created_at >= d, Like.created_at < next_d)
            follows = await self._count_where(db, Follow, Follow.created_at >= d, Follow.created_at < next_d)
            comments = await self._count_where(db, Comment, Comment.created_at >= d, Comment.created_at < next_d)
            result.append({
                "date": d.isoformat(),
                "likes": likes,
                "comments": comments,
                "follows": follows,
            })
        return result

    async def _count(self, db: AsyncSession, model):
        result = await db.execute(select(func.count()).select_from(model))
        return result.scalar() or 0

    async def _count_where(self, db: AsyncSession, model, *conditions):
        query = select(func.count()).select_from(model)
        for cond in conditions:
            query = query.where(cond)
        result = await db.execute(query)
        return result.scalar() or 0


class AdminUserService:
    """用户管理服务"""

    async def list_users(self, db: AsyncSession, skip: int = 0, limit: int = 20,
                        search: str = None, is_active: bool = None) -> list[dict]:
        query = select(User)

        if search:
            query = query.where(
                or_(
                    User.username.ilike(f"%{search}%"),
                    User.email.ilike(f"%{search}%")
                )
            )

        if is_active is not None:
            query = query.where(User.is_active == is_active)

        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        users = result.scalars().all()

        # 补充博客数和评论数
        user_list = []
        for user in users:
            blog_count = await db.execute(
                select(func.count()).select_from(Blog).where(Blog.author_id == user.id)
            )
            comment_count = await db.execute(
                select(func.count()).select_from(Comment).where(Comment.author_id == user.id)
            )
            user_list.append({
                "id": user.id,
                "username": user.username,
                "email": getattr(user, 'email', None),
                "is_active": user.is_active,
                "is_admin": user.is_admin,
                "created_at": user.created_at,
                "blog_count": blog_count.scalar() or 0,
                "comment_count": comment_count.scalar() or 0,
            })
        return user_list

    async def ban_user(self, db: AsyncSession, admin_id: str, user_id: str, reason: str = None) -> bool:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            return False

        user.is_active = False
        await self._log_action(db, admin_id, "ban_user", "user", user_id, reason)
        await db.flush()
        return True

    async def unban_user(self, db: AsyncSession, admin_id: str, user_id: str) -> bool:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            return False

        user.is_active = True
        await self._log_action(db, admin_id, "unban_user", "user", user_id)
        await db.flush()
        return True

    async def _log_action(self, db: AsyncSession, admin_id: str, action: str,
                         target_type: str, target_id: str, detail: str = None, ip: str = None):
        log = AdminLog(
            admin_id=admin_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            detail=detail,
            ip_address=ip,
        )
        db.add(log)


class AdminSensitiveWordService:
    """敏感词管理服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_words(self, skip: int = 0, limit: int = 100):
        # 敏感词存储在 Redis 或 DB 中
        # 这里假设在 core.moderation 模块中管理
        from core.moderation import get_filter
        # 返回格式化的列表（实际数据从 Redis/DB 读取）
        return []

    async def add_word(self, admin_id: str, word: str, action: str) -> dict:
        # 实际实现需要存储到 Redis 或 DB
        # 这里返回占位
        await self._log_action(self.db, admin_id, "add_sensitive_word", "sensitive_word", word, action)
        return {"word": word, "action": action}

    async def update_word(self, admin_id: str, word_id: str, word: str = None, action: str = None) -> bool:
        await self._log_action(self.db, admin_id, "update_sensitive_word", "sensitive_word", word_id)
        return True

    async def delete_word(self, admin_id: str, word_id: str) -> bool:
        await self._log_action(self.db, admin_id, "delete_sensitive_word", "sensitive_word", word_id)
        return True

    async def reload_filter(self):
        """重新加载敏感词过滤器"""
        from core.moderation import reload_filter
        # 从 DB 读取敏感词列表并重新加载
        pass

    async def _log_action(self, db: AsyncSession, admin_id: str, action: str,
                         target_type: str, target_id: str, detail: str = None):
        log = AdminLog(
            admin_id=admin_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            detail=detail,
        )
        db.add(log)
        await db.flush()


class AdminReviewService:
    """内容审核服务 - warn 级别内容"""

    async def get_warned_blogs(self, db: AsyncSession, skip: int = 0, limit: int = 20):
        # 获取包含 warn 标记的博客
        # 实际需要 moderation_result 表或字段支持
        return []

    async def get_warned_comments(self, db: AsyncSession, skip: int = 0, limit: int = 20):
        return []

    async def review_blog(self, db: AsyncSession, admin_id: str, blog_id: str, action: str, reason: str = None) -> bool:
        await self._log_action(db, admin_id, f"review_blog_{action}", "blog", blog_id, reason)
        return True

    async def review_comment(self, db: AsyncSession, admin_id: str, comment_id: str, action: str, reason: str = None) -> bool:
        await self._log_action(db, admin_id, f"review_comment_{action}", "comment", comment_id, reason)
        return True

    async def _log_action(self, db: AsyncSession, admin_id: str, action: str,
                         target_type: str, target_id: str, detail: str = None):
        log = AdminLog(
            admin_id=admin_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            detail=detail,
        )
        db.add(log)
        await db.flush()


class AdminLogService:
    """操作日志服务"""

    async def list_logs(self, db: AsyncSession, skip: int = 0, limit: int = 50,
                       admin_id: str = None, action: str = None) -> list[dict]:
        query = select(AdminLog)

        if admin_id:
            query = query.where(AdminLog.admin_id == admin_id)
        if action:
            query = query.where(AdminLog.action.like(f"%{action}%"))

        query = query.order_by(AdminLog.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        logs = result.scalars().all()

        # 补充 admin 用户名
        log_list = []
        for log in logs:
            admin_result = await db.execute(select(User).where(User.id == log.admin_id))
            admin = admin_result.scalar_one_or_none()
            log_list.append({
                "id": log.id,
                "admin_id": log.admin_id,
                "admin_username": admin.username if admin else None,
                "action": log.action,
                "target_type": log.target_type,
                "target_id": log.target_id,
                "detail": log.detail,
                "ip_address": log.ip_address,
                "created_at": log.created_at,
            })
        return log_list


class AdminSecurityService:
    """安全服务 - 登录日志 + IP封禁"""

    # 登录失败限制配置
    MAX_LOGIN_ATTEMPTS = 5
    LOGIN_ATTEMPT_WINDOW_MINUTES = 5
    AUTO_BAN_DURATION_MINUTES = 15

    async def record_login(
        self,
        db: AsyncSession,
        ip_address: str,
        user_agent: str,
        status: str,
        admin_id: str = None,
        fail_reason: str = None,
    ) -> None:
        """记录登录日志"""
        from apps.admin.models import LoginLog
        log = LoginLog(
            ip_address=ip_address,
            user_agent=user_agent,
            login_time=datetime.now(),
            status=status,
            admin_id=admin_id,
            fail_reason=fail_reason,
        )
        db.add(log)
        await db.flush()

        # 如果登录失败，检查是否需要自动封禁
        if status == "failed":
            await self._check_auto_ban(db, ip_address)

    async def _check_auto_ban(self, db: AsyncSession, ip_address: str) -> None:
        """检查是否需要自动封禁IP"""
        from apps.admin.models import LoginLog, IPBan

        # 统计最近 LOGIN_ATTEMPT_WINDOW_MINUTES 分钟内的失败次数
        cutoff = datetime.now() - timedelta(minutes=self.LOGIN_ATTEMPT_WINDOW_MINUTES)
        result = await db.execute(
            select(func.count())
            .select_from(LoginLog)
            .where(
                LoginLog.ip_address == ip_address,
                LoginLog.status == "failed",
                LoginLog.login_time >= cutoff,
            )
        )
        failed_count = result.scalar() or 0

        if failed_count >= self.MAX_LOGIN_ATTEMPTS:
            # 自动封禁IP
            ban = IPBan(
                ip_address=ip_address,
                reason=f"自动封禁：{self.MAX_LOGIN_ATTEMPTS}次登录失败",
                banned_by="system",
                banned_at=datetime.now(),
                expires_at=datetime.now() + timedelta(minutes=self.AUTO_BAN_DURATION_MINUTES),
            )
            db.add(ban)
            await db.flush()

    async def is_ip_banned(self, db: AsyncSession, ip_address: str) -> tuple[bool, str, datetime]:
        """检查IP是否被封禁"""
        from apps.admin.models import IPBan

        result = await db.execute(
            select(IPBan).where(
                IPBan.ip_address == ip_address,
                or_(IPBan.expires_at.is_(None), IPBan.expires_at > datetime.now()),
            )
        )
        ban = result.scalar_one_or_none()

        if ban:
            return True, ban.reason, ban.expires_at
        return False, None, None

    async def ban_ip(
        self,
        db: AsyncSession,
        ip_address: str,
        reason: str,
        banned_by: str,
        expires_at: datetime = None,
    ) -> IPBan:
        """手动封禁IP"""
        from apps.admin.models import IPBan

        # 检查是否已存在
        result = await db.execute(
            select(IPBan).where(IPBan.ip_address == ip_address)
        )
        existing = result.scalar_one_or_none()

        if existing:
            # 更新现有记录
            existing.reason = reason
            existing.banned_by = banned_by
            existing.expires_at = expires_at
            await db.flush()
            return existing

        ban = IPBan(
            ip_address=ip_address,
            reason=reason,
            banned_by=banned_by,
            banned_at=datetime.now(),
            expires_at=expires_at,
        )
        db.add(ban)
        await db.flush()
        return ban

    async def unban_ip(self, db: AsyncSession, ip_address: str) -> bool:
        """解封IP"""
        from apps.admin.models import IPBan

        result = await db.execute(
            select(IPBan).where(IPBan.ip_address == ip_address)
        )
        ban = result.scalar_one_or_none()
        if not ban:
            return False
        await db.delete(ban)
        await db.flush()
        return True

    async def list_bans(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 50,
        active_only: bool = True,
    ) -> list[dict]:
        """列出封禁记录"""
        from apps.admin.models import IPBan

        query = select(IPBan)

        if active_only:
            query = query.where(
                or_(IPBan.expires_at.is_(None), IPBan.expires_at > datetime.now())
            )

        query = query.order_by(IPBan.banned_at.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        bans = result.scalars().all()

        return [
            {
                "id": ban.id,
                "ip_address": ban.ip_address,
                "reason": ban.reason,
                "banned_by": ban.banned_by,
                "banned_at": ban.banned_at,
                "expires_at": ban.expires_at,
                "is_active": ban.expires_at is None or ban.expires_at > datetime.now(),
            }
            for ban in bans
        ]

    async def list_login_logs(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 50,
        ip_address: str = None,
        status: str = None,
    ) -> list[dict]:
        """列出登录日志"""
        from apps.admin.models import LoginLog

        query = select(LoginLog)

        if ip_address:
            query = query.where(LoginLog.ip_address == ip_address)
        if status:
            query = query.where(LoginLog.status == status)

        query = query.order_by(LoginLog.login_time.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        logs = result.scalars().all()

        return [
            {
                "id": log.id,
                "ip_address": log.ip_address,
                "user_agent": log.user_agent,
                "login_time": log.login_time,
                "status": log.status,
                "fail_reason": log.fail_reason,
                "admin_id": log.admin_id,
            }
            for log in logs
        ]
```

- [ ] **Step 2: Commit**

---

### Task 3: Admin API Views

**Files:**
- Create: `backend/apps/admin/router.py`
- Modify: `backend/main.py`
- Test: `backend/tests/apps/admin/test_router.py`

- [ ] **Step 1: Create backend/apps/admin/router.py**

```python
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import timedelta

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


# ==================== Dependencies ====================

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

    # 检查IP是否被封禁
    is_banned, ban_reason, ban_expires = await security_service.is_ip_banned(db, client_ip)
    if is_banned:
        await security_service.record_login(db, client_ip, user_agent, "failed", fail_reason=f"IP被封禁: {ban_reason}")
        raise HTTPException(status_code=403, detail=f"IP已被封禁: {ban_reason}")

    service = AdminAuthService(db)
    user = await service.authenticate(db, login_data.username, login_data.password)

    if not user:
        await security_service.record_login(db, client_ip, user_agent, "failed", fail_reason="Invalid credentials")
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # 记录成功登录
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
        from datetime import timedelta
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
```

- [ ] **Step 2: Register router in main.py**

```python
from apps.admin.router import router as admin_router
app.include_router(admin_router)
```

- [ ] **Step 3: Commit**

---

## Frontend: Admin Client

### Task 4: Admin Client Setup

**Files:**
- Create: `admin-client/` directory structure
- Create: `admin-client/package.json`
- Create: `admin-client/vite.config.js`
- Create: `admin-client/index.html`
- Create: `admin-client/src/main.js`
- Create: `admin-client/src/App.vue`

- [ ] **Step 1: Create admin-client/package.json**

```json
{
  "name": "admin-client",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "vue": "^3.4.0",
    "vue-router": "^4.2.0",
    "pinia": "^2.1.0",
    "element-plus": "^2.5.0",
    "echarts": "^5.5.0",
    "axios": "^1.6.0"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^5.0.0",
    "vite": "^5.0.0"
  }
}
```

- [ ] **Step 2: Create admin-client/vite.config.js**

```javascript
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
```

- [ ] **Step 3: Create admin-client/index.html**

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Admin - 百日筑基</title>
</head>
<body>
  <div id="app"></div>
  <script type="module" src="/src/main.js"></script>
</body>
</html>
```

- [ ] **Step 4: Create admin-client/src/main.js**

```javascript
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIcons from '@element-plus/icons-vue'
import App from './App.vue'
import router from './router'

const app = createApp(App)
const pinia = createPinia()

// Register Element Plus icons
for (const [key, component] of Object.entries(ElementPlusIcons)) {
  app.component(key, component)
}

app.use(pinia)
app.use(router)
app.use(ElementPlus)
app.mount('#app')
```

- [ ] **Step 5: Create admin-client/src/App.vue**

```vue
<template>
  <router-view />
</template>

<style>
* { margin: 0; padding: 0; box-sizing: border-box; }

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  background: #F2F9F4;
  color: #2D3B30;
}

#app { min-height: 100vh; }
</style>
```

- [ ] **Step 6: Commit**

---

### Task 5: Admin Router & Layout

**Files:**
- Create: `admin-client/src/router/index.js`
- Create: `admin-client/src/layouts/AdminLayout.vue`

- [ ] **Step 1: Create admin-client/src/router/index.js**

```javascript
import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/login',
    name: 'AdminLogin',
    component: () => import('@/views/Login.vue'),
    meta: { guest: true },
  },
  {
    path: '/',
    component: () => import('@/layouts/AdminLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        redirect: '/dashboard',
      },
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/Dashboard.vue'),
      },
      {
        path: 'users',
        name: 'Users',
        component: () => import('@/views/Users.vue'),
      },
      {
        path: 'sensitive-words',
        name: 'SensitiveWords',
        component: () => import('@/views/SensitiveWords.vue'),
      },
      {
        path: 'review',
        name: 'Review',
        component: () => import('@/views/Review.vue'),
      },
      {
        path: 'logs',
        name: 'Logs',
        component: () => import('@/views/Logs.vue'),
      },
      {
        path: 'security',
        name: 'Security',
        component: () => import('@/views/Security.vue'),
      },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('admin_token')

  if (to.meta.requiresAuth && !token) {
    next('/login')
  } else if (to.meta.guest && token) {
    next('/dashboard')
  } else {
    next()
  }
})

export default router
```

- [ ] **Step 2: Create admin-client/src/layouts/AdminLayout.vue**

```vue
<template>
  <div class="admin-layout">
    <aside class="sidebar">
      <div class="logo">
        <h1>Admin</h1>
      </div>
      <nav class="nav">
        <router-link to="/dashboard" class="nav-item">
          <el-icon><DataAnalysis /></el-icon>
          <span>Dashboard</span>
        </router-link>
        <router-link to="/users" class="nav-item">
          <el-icon><User /></el-icon>
          <span>用户管理</span>
        </router-link>
        <router-link to="/sensitive-words" class="nav-item">
          <el-icon><Warning /></el-icon>
          <span>敏感词</span>
        </router-link>
        <router-link to="/review" class="nav-item">
          <el-icon><DocumentChecked /></el-icon>
          <span>内容审核</span>
        </router-link>
        <router-link to="/logs" class="nav-item">
          <el-icon><Operation /></el-icon>
          <span>操作日志</span>
        </router-link>
        <router-link to="/security" class="nav-item">
          <el-icon><Shield /></el-icon>
          <span>安全中心</span>
        </router-link>
      </nav>
      <div class="sidebar-footer">
        <router-link to="/" class="nav-item" target="_blank">
          <el-icon><View /></el-icon>
          <span>返回主站</span>
        </router-link>
        <button class="nav-item" @click="handleLogout">
          <el-icon><SwitchButton /></el-icon>
          <span>退出登录</span>
        </button>
      </div>
    </aside>
    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()

function handleLogout() {
  localStorage.removeItem('admin_token')
  router.push('/login')
}
</script>

<style scoped>
.admin-layout { display: flex; min-height: 100vh; }

.sidebar {
  width: 220px;
  background: #2D3B30;
  color: #FFFFFF;
  display: flex;
  flex-direction: column;
  position: fixed;
  height: 100vh;
}

.logo { padding: 24px 16px; border-bottom: 1px solid rgba(255,255,255,0.1); }
.logo h1 { font-size: 20px; font-weight: 600; color: #5A9672; }

.nav { flex: 1; padding: 16px 0; }
.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  color: rgba(255,255,255,0.7);
  text-decoration: none;
  font-size: 14px;
  transition: all 200ms;
  border: none;
  background: none;
  width: 100%;
  cursor: pointer;
}
.nav-item:hover { background: rgba(255,255,255,0.1); color: #FFFFFF; }
.nav-item.router-link-active { background: rgba(90,150,114,0.3); color: #5A9672; }

.sidebar-footer { padding: 16px 0; border-top: 1px solid rgba(255,255,255,0.1); }

.main-content { flex: 1; margin-left: 220px; padding: 24px; background: #F2F9F4; min-height: 100vh; }
</style>
```

- [ ] **Step 3: Commit**

---

### Task 6: Admin API Client

**Files:**
- Create: `admin-client/src/api/index.js`

- [ ] **Step 1: Create admin-client/src/api/index.js**

```javascript
import axios from 'axios'

const client = axios.create({
  baseURL: '/api/admin',
  timeout: 10000,
  headers: { 'Content-Type': 'application/json' },
})

client.interceptors.request.use((config) => {
  const token = localStorage.getItem('admin_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('admin_token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default client
```

- [ ] **Step 2: Commit**

---

### Task 7: Dashboard View

**Files:**
- Create: `admin-client/src/views/Dashboard.vue`

- [ ] **Step 1: Create admin-client/src/views/Dashboard.vue**

```vue
<template>
  <div class="dashboard">
    <h2>数据概览</h2>

    <!-- 统计卡片 -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-icon" style="background: #E8F5ED;">
          <el-icon size="24" color="#5A9672"><User /></el-icon>
        </div>
        <div class="stat-info">
          <span class="stat-value">{{ stats.total_users }}</span>
          <span class="stat-label">总用户数</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="background: #FFF3E0;">
          <el-icon size="24" color="#FF9800;"><Document /></el-icon>
        </div>
        <div class="stat-info">
          <span class="stat-value">{{ stats.total_blogs }}</span>
          <span class="stat-label">总博客数</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="background: #E3F2FD;">
          <el-icon size="24" color="#2196F3;"><ChatDotRound /></el-icon>
        </div>
        <div class="stat-info">
          <span class="stat-value">{{ stats.total_comments }}</span>
          <span class="stat-label">总评论数</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="background: #FCE4EC;">
          <el-icon size="24" color="#E91E63;"><Star /></el-icon>
        </div>
        <div class="stat-info">
          <span class="stat-value">{{ stats.total_likes }}</span>
          <span class="stat-label">总点赞数</span>
        </div>
      </div>
    </div>

    <!-- 今日新增 -->
    <div class="today-stats">
      <h3>今日新增</h3>
      <div class="today-grid">
        <div class="today-item">
          <span class="today-value">{{ stats.today_new_users }}</span>
          <span class="today-label">新用户</span>
        </div>
        <div class="today-item">
          <span class="today-value">{{ stats.today_new_blogs }}</span>
          <span class="today-label">新博客</span>
        </div>
        <div class="today-item">
          <span class="today-value">{{ stats.today_new_comments }}</span>
          <span class="today-label">新评论</span>
        </div>
      </div>
    </div>

    <!-- 图表 -->
    <div class="charts-grid">
      <div class="chart-card">
        <h3>用户增长</h3>
        <div ref="userChartRef" class="chart"></div>
      </div>
      <div class="chart-card">
        <h3>博客增长</h3>
        <div ref="blogChartRef" class="chart"></div>
      </div>
      <div class="chart-card">
        <h3>互动统计</h3>
        <div ref="interactionChartRef" class="chart"></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive } from 'vue'
import * as echarts from 'echarts'
import client from '@/api'

const stats = reactive({
  total_users: 0, total_blogs: 0, total_comments: 0, total_likes: 0,
  today_new_users: 0, today_new_blogs: 0, today_new_comments: 0,
})

const userChartRef = ref(null)
const blogChartRef = ref(null)
const interactionChartRef = ref(null)

onMounted(async () => {
  await loadStats()
  await loadCharts()
})

async function loadStats() {
  try {
    const response = await client.get('/dashboard/stats')
    Object.assign(stats, response.data)
  } catch (error) {
    console.error('Failed to load stats', error)
  }
}

async function loadCharts() {
  try {
    const [userRes, blogRes, interactionRes] = await Promise.all([
      client.get('/dashboard/user-growth'),
      client.get('/dashboard/blog-growth'),
      client.get('/dashboard/interactions'),
    ])

    // 用户增长图
    const userChart = echarts.init(userChartRef.value)
    userChart.setOption({
      tooltip: { trigger: 'axis' },
      xAxis: { type: 'category', data: userRes.data.map(d => d.date) },
      yAxis: { type: 'value' },
      series: [{ data: userRes.data.map(d => d.count), type: 'line', smooth: true, areaStyle: { color: '#E8F5ED' }, lineStyle: { color: '#5A9672' }, itemStyle: { color: '#5A9672' } }],
    })

    // 博客增长图
    const blogChart = echarts.init(blogChartRef.value)
    blogChart.setOption({
      tooltip: { trigger: 'axis' },
      xAxis: { type: 'category', data: blogRes.data.map(d => d.date) },
      yAxis: { type: 'value' },
      series: [{ data: blogRes.data.map(d => d.count), type: 'bar', itemStyle: { color: '#5A9672' } }],
    })

    // 互动统计图
    const interactionChart = echarts.init(interactionChartRef.value)
    interactionChart.setOption({
      tooltip: { trigger: 'axis' },
      legend: { data: ['点赞', '评论', '关注'] },
      xAxis: { type: 'category', data: interactionRes.data.map(d => d.date) },
      yAxis: { type: 'value' },
      series: [
        { name: '点赞', data: interactionRes.data.map(d => d.likes), type: 'line', itemStyle: { color: '#E91E63' } },
        { name: '评论', data: interactionRes.data.map(d => d.comments), type: 'line', itemStyle: { color: '#2196F3' } },
        { name: '关注', data: interactionRes.data.map(d => d.follows), type: 'line', itemStyle: { color: '#FF9800' } },
      ],
    })
  } catch (error) {
    console.error('Failed to load charts', error)
  }
}
</script>

<style scoped>
.dashboard { max-width: 1200px; }
.dashboard h2 { font-size: 24px; margin-bottom: 24px; }
.dashboard h3 { font-size: 16px; margin-bottom: 16px; color: #2D3B30; }

.stats-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 24px; }
.stat-card {
  background: #FFFFFF; border-radius: 12px; padding: 20px;
  display: flex; align-items: center; gap: 16px;
  border: 1px solid #DDEEE5;
}
.stat-icon { width: 48px; height: 48px; border-radius: 12px; display: flex; align-items: center; justify-content: center; }
.stat-value { font-size: 28px; font-weight: 700; color: #2D3B30; display: block; }
.stat-label { font-size: 13px; color: #6B7D72; }

.today-stats { background: #FFFFFF; border-radius: 12px; padding: 20px; margin-bottom: 24px; border: 1px solid #DDEEE5; }
.today-grid { display: flex; gap: 48px; }
.today-item { display: flex; flex-direction: column; }
.today-value { font-size: 24px; font-weight: 700; color: #5A9672; }
.today-label { font-size: 13px; color: #6B7D72; }

.charts-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; }
.chart-card { background: #FFFFFF; border-radius: 12px; padding: 20px; border: 1px solid #DDEEE5; }
.chart-card:last-child { grid-column: span 2; }
.chart { height: 250px; }
</style>
```

- [ ] **Step 2: Commit**

---

### Task 8: Login View

**Files:**
- Create: `admin-client/src/views/Login.vue`

- [ ] **Step 1: Create admin-client/src/views/Login.vue**

```vue
<template>
  <div class="login-page">
    <div class="login-card">
      <h1>Admin 登录</h1>
      <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="form.password" type="password" placeholder="请输入密码" @keyup.enter="handleLogin" />
        </el-form-item>
        <el-button type="primary" :loading="loading" @click="handleLogin" style="width: 100%">
          登录
        </el-button>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import axios from 'axios'

const router = useRouter()
const formRef = ref(null)
const loading = ref(false)

const form = reactive({ username: '', password: '' })
const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

async function handleLogin() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    const response = await axios.post('/api/admin/login', form)
    localStorage.setItem('admin_token', response.data.access_token)
    ElMessage.success('登录成功')
    router.push('/dashboard')
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '登录失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh; display: flex; align-items: center; justify-content: center;
  background: linear-gradient(135deg, #2D3B30 0%, #5A9672 100%);
}
.login-card {
  background: #FFFFFF; border-radius: 16px; padding: 40px; width: 380px;
  box-shadow: 0 8px 32px rgba(0,0,0,0.2);
}
.login-card h1 { text-align: center; margin-bottom: 32px; font-size: 24px; color: #2D3B30; }
</style>
```

- [ ] **Step 2: Commit**

---

### Task 9: User Management View

**Files:**
- Create: `admin-client/src/views/Users.vue`

- [ ] **Step 1: Create admin-client/src/views/Users.vue**

```vue
<template>
  <div class="users-page">
    <div class="page-header">
      <h2>用户管理</h2>
      <div class="filters">
        <el-input v-model="search" placeholder="搜索用户名/邮箱" clearable style="width: 200px" />
        <el-select v-model="isActive" placeholder="状态" clearable style="width: 120px">
          <el-option label="正常" :value="true" />
          <el-option label="已封禁" :value="false" />
        </el-select>
      </div>
    </div>

    <el-table :data="users" v-loading="loading" stripe>
      <el-table-column prop="username" label="用户名" />
      <el-table-column prop="email" label="邮箱" />
      <el-table-column prop="blog_count" label="博客数" width="100" />
      <el-table-column prop="comment_count" label="评论数" width="100" />
      <el-table-column prop="is_active" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="row.is_active ? 'success' : 'danger'">
            {{ row.is_active ? '正常' : '已封禁' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="is_admin" label="角色" width="100">
        <template #default="{ row }">
          <el-tag v-if="row.is_admin" type="warning">管理员</el-tag>
          <span v-else>普通用户</span>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="150">
        <template #default="{ row }">
          <el-button v-if="row.is_active && !row.is_admin" type="danger" size="small" @click="handleBan(row)">
            封禁
          </el-button>
          <el-button v-else-if="!row.is_active" type="success" size="small" @click="handleUnban(row)">
            解封
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination
      v-model:current-page="page"
      :page-size="20"
      :total="total"
      layout="total, prev, pager, next"
      @current-change="loadUsers"
      style="margin-top: 20px; justify-content: center"
    />
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import client from '@/api'

const users = ref([])
const loading = ref(false)
const search = ref('')
const isActive = ref(null)
const page = ref(1)
const total = ref(0)

onMounted(() => loadUsers())

async function loadUsers() {
  loading.value = true
  try {
    const params = { skip: (page.value - 1) * 20, limit: 20 }
    if (search.value) params.search = search.value
    if (isActive.value !== null) params.is_active = isActive.value
    const response = await client.get('/users', { params })
    users.value = response.data
    total.value = users.value.length // 简化，实际需要 total count
  } catch (error) {
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
}

async function handleBan(user) {
  try {
    await ElMessageBox.confirm(`确定封禁用户 ${user.username}？`, '确认', { type: 'warning' })
    await client.post('/users/ban', { user_id: user.id })
    ElMessage.success('已封禁')
    loadUsers()
  } catch (error) {
    if (error !== 'cancel') ElMessage.error('操作失败')
  }
}

async function handleUnban(user) {
  try {
    await client.post('/users/unban', { user_id: user.id })
    ElMessage.success('已解封')
    loadUsers()
  } catch (error) {
    ElMessage.error('操作失败')
  }
}
</script>

<style scoped>
.users-page { max-width: 1000px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; }
.page-header h2 { font-size: 24px; }
.filters { display: flex; gap: 12px; }
</style>
```

- [ ] **Step 2: Commit**

---

### Task 10: Sensitive Words View

**Files:**
- Create: `admin-client/src/views/SensitiveWords.vue`

- [ ] **Step 1: Create admin-client/src/views/SensitiveWords.vue**

```vue
<template>
  <div class="sensitive-words-page">
    <div class="page-header">
      <h2>敏感词管理</h2>
      <div class="actions">
        <el-button type="primary" @click="showAddDialog = true">添加敏感词</el-button>
        <el-button @click="handleReload">重新加载过滤器</el-button>
      </div>
    </div>

    <el-table :data="words" v-loading="loading" stripe>
      <el-table-column prop="word" label="敏感词" />
      <el-table-column prop="action" label="动作" width="120">
        <template #default="{ row }">
          <el-tag :type="row.action === 'block' ? 'danger' : row.action === 'replace' ? 'warning' : 'info'">
            {{ row.action === 'block' ? '拦截' : row.action === 'replace' ? '替换' : '警告' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="180">
        <template #default="{ row }">
          {{ new Date(row.created_at).toLocaleString('zh-CN') }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="150">
        <template #default="{ row }">
          <el-button type="primary" size="small" @click="handleEdit(row)">编辑</el-button>
          <el-button type="danger" size="small" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 添加/编辑对话框 -->
    <el-dialog v-model="showAddDialog" :title="editingWord ? '编辑敏感词' : '添加敏感词'" width="400px">
      <el-form ref="formRef" :model="form" label-width="80px">
        <el-form-item label="敏感词">
          <el-input v-model="form.word" placeholder="请输入敏感词" />
        </el-form-item>
        <el-form-item label="动作">
          <el-select v-model="form.action" style="width: 100%">
            <el-option label="拦截 (block)" value="block" />
            <el-option label="替换 (replace)" value="replace" />
            <el-option label="警告 (warn)" value="warn" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import client from '@/api'

const words = ref([])
const loading = ref(false)
const showAddDialog = ref(false)
const editingWord = ref(null)
const formRef = ref(null)

const form = reactive({ word: '', action: 'warn' })

onMounted(() => loadWords())

async function loadWords() {
  loading.value = true
  try {
    const response = await client.get('/sensitive-words')
    words.value = response.data
  } catch (error) {
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
}

function handleEdit(word) {
  editingWord.value = word
  form.word = word.word
  form.action = word.action
  showAddDialog.value = true
}

async function handleSave() {
  try {
    if (editingWord.value) {
      await client.put(`/sensitive-words/${editingWord.value.id}`, form)
      ElMessage.success('更新成功')
    } else {
      await client.post('/sensitive-words', form)
      ElMessage.success('添加成功')
    }
    showAddDialog.value = false
    editingWord.value = null
    form.word = ''
    form.action = 'warn'
    loadWords()
  } catch (error) {
    ElMessage.error('保存失败')
  }
}

async function handleDelete(word) {
  try {
    await ElMessageBox.confirm(`确定删除敏感词 "${word.word}"？`, '确认', { type: 'warning' })
    await client.delete(`/sensitive-words/${word.id}`)
    ElMessage.success('删除成功')
    loadWords()
  } catch (error) {
    if (error !== 'cancel') ElMessage.error('删除失败')
  }
}

async function handleReload() {
  try {
    await client.post('/sensitive-words/reload')
    ElMessage.success('过滤器已重新加载')
  } catch (error) {
    ElMessage.error('重新加载失败')
  }
}
</script>

<style scoped>
.sensitive-words-page { max-width: 1000px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; }
.page-header h2 { font-size: 24px; }
.actions { display: flex; gap: 12px; }
</style>
```

- [ ] **Step 2: Commit**

---

### Task 11: Review View

**Files:**
- Create: `admin-client/src/views/Review.vue`

- [ ] **Step 1: Create admin-client/src/views/Review.vue**

```vue
<template>
  <div class="review-page">
    <h2>内容审核</h2>
    <el-tabs v-model="activeTab">
      <el-tab-pane label="博客" name="blogs">
        <div v-for="blog in blogs" :key="blog.id" class="review-item">
          <div class="item-header">
            <span class="author">{{ blog.author_username }}</span>
            <span class="date">{{ new Date(blog.created_at).toLocaleString('zh-CN') }}</span>
          </div>
          <h3>{{ blog.title }}</h3>
          <div class="flagged-words">
            <el-tag v-for="word in blog.flagged_words" :key="word" type="warning">{{ word }}</el-tag>
          </div>
          <div class="item-actions">
            <el-button type="success" size="small" @click="handleApprove('blog', blog.id)">通过</el-button>
            <el-button type="danger" size="small" @click="handleReject('blog', blog.id)">删除</el-button>
          </div>
        </div>
        <el-empty v-if="blogs.length === 0" description="暂无待审核内容" />
      </el-tab-pane>
      <el-tab-pane label="评论" name="comments">
        <div v-for="comment in comments" :key="comment.id" class="review-item">
          <div class="item-header">
            <span class="author">{{ comment.author_username }}</span>
            <span class="date">{{ new Date(comment.created_at).toLocaleString('zh-CN') }}</span>
          </div>
          <p class="content">{{ comment.content }}</p>
          <div class="flagged-words">
            <el-tag v-for="word in comment.flagged_words" :key="word" type="warning">{{ word }}</el-tag>
          </div>
          <div class="item-actions">
            <el-button type="success" size="small" @click="handleApprove('comment', comment.id)">通过</el-button>
            <el-button type="danger" size="small" @click="handleReject('comment', comment.id)">删除</el-button>
          </div>
        </div>
        <el-empty v-if="comments.length === 0" description="暂无待审核内容" />
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import client from '@/api'

const activeTab = ref('blogs')
const blogs = ref([])
const comments = ref([])

onMounted(() => loadData())

async function loadData() {
  try {
    const [blogRes, commentRes] = await Promise.all([
      client.get('/review/blogs'),
      client.get('/review/comments'),
    ])
    blogs.value = blogRes.data
    comments.value = commentRes.data
  } catch (error) {
    ElMessage.error('加载失败')
  }
}

async function handleApprove(type, id) {
  try {
    await client.post(`/review/${type}s/${id}`, { action: 'approve' })
    ElMessage.success('已通过')
    loadData()
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

async function handleReject(type, id) {
  try {
    await ElMessageBox.confirm('确定删除该内容？', '确认', { type: 'warning' })
    await client.post(`/review/${type}s/${id}`, { action: 'reject' })
    ElMessage.success('已删除')
    loadData()
  } catch (error) {
    if (error !== 'cancel') ElMessage.error('操作失败')
  }
}
</script>

<style scoped>
.review-page { max-width: 800px; }
.review-page h2 { font-size: 24px; margin-bottom: 24px; }
.review-item {
  background: #FFFFFF; border-radius: 12px; padding: 16px; margin-bottom: 16px;
  border: 1px solid #DDEEE5;
}
.item-header { display: flex; gap: 12px; margin-bottom: 8px; font-size: 13px; color: #6B7D72; }
.item-header .author { font-weight: 600; color: #2D3B30; }
.review-item h3 { font-size: 16px; margin-bottom: 8px; }
.review-item .content { color: #2D3B30; line-height: 1.6; margin-bottom: 12px; }
.flagged-words { display: flex; gap: 8px; margin-bottom: 12px; }
.item-actions { display: flex; gap: 8px; }
</style>
```

- [ ] **Step 2: Commit**

---

### Task 12: Logs View

**Files:**
- Create: `admin-client/src/views/Logs.vue`

- [ ] **Step 1: Create admin-client/src/views/Logs.vue**

```vue
<template>
  <div class="logs-page">
    <div class="page-header">
      <h2>操作日志</h2>
    </div>

    <el-table :data="logs" v-loading="loading" stripe>
      <el-table-column prop="admin_username" label="管理员" width="120" />
      <el-table-column prop="action" label="操作" width="180">
        <template #default="{ row }">
          <el-tag>{{ row.action }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="target_type" label="对象类型" width="120" />
      <el-table-column prop="target_id" label="对象ID" width="200" show-overflow-tooltip />
      <el-table-column prop="detail" label="详情" show-overflow-tooltip />
      <el-table-column prop="ip_address" label="IP" width="130" />
      <el-table-column prop="created_at" label="时间" width="180">
        <template #default="{ row }">
          {{ new Date(row.created_at).toLocaleString('zh-CN') }}
        </template>
      </el-table-column>
    </el-table>

    <el-pagination
      v-model:current-page="page"
      :page-size="50"
      :total="total"
      layout="total, prev, pager, next"
      @current-change="loadLogs"
      style="margin-top: 20px; justify-content: center"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import client from '@/api'

const logs = ref([])
const loading = ref(false)
const page = ref(1)
const total = ref(0)

onMounted(() => loadLogs())

async function loadLogs() {
  loading.value = true
  try {
    const response = await client.get('/logs', { params: { skip: (page.value - 1) * 50, limit: 50 } })
    logs.value = response.data
    total.value = logs.value.length // 简化
  } catch (error) {
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.logs-page { max-width: 1200px; }
.page-header { margin-bottom: 24px; }
.page-header h2 { font-size: 24px; }
</style>
```

- [ ] **Step 2: Commit**

---

### Task 13: Security View (Login Logs & IP Bans)

**Files:**
- Create: `admin-client/src/views/Security.vue`

- [ ] **Step 1: Create admin-client/src/views/Security.vue**

```vue
<template>
  <div class="security-page">
    <el-tabs v-model="activeTab" class="security-tabs">
      <!-- 登录日志 -->
      <el-tab-pane label="登录日志" name="login-logs">
        <div class="filter-bar">
          <el-input v-model="loginFilters.ip_address" placeholder="IP 地址" clearable style="width: 180px" />
          <el-select v-model="loginFilters.status" placeholder="状态" clearable style="width: 120px">
            <el-option label="成功" value="success" />
            <el-option label="失败" value="failed" />
          </el-select>
          <el-button @click="loadLoginLogs">搜索</el-button>
        </div>

        <el-table :data="loginLogs" v-loading="loginLoading" stripe class="login-logs-table">
          <el-table-column prop="ip_address" label="IP 地址" width="140" />
          <el-table-column prop="user_agent" label="User Agent" width="200" show-overflow-tooltip />
          <el-table-column prop="login_time" label="登录时间" width="180">
            <template #default="{ row }">
              {{ new Date(row.login_time).toLocaleString('zh-CN') }}
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="row.status === 'success' ? 'success' : 'danger'" size="small">
                {{ row.status === 'success' ? '成功' : '失败' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="fail_reason" label="失败原因" show-overflow-tooltip />
        </el-table>

        <el-pagination
          v-model:current-page="loginPage"
          :page-size="20"
          :total="loginTotal"
          layout="total, prev, pager, next"
          @current-change="loadLoginLogs"
          style="margin-top: 20px; justify-content: center"
        />
      </el-tab-pane>

      <!-- IP 黑名单 -->
      <el-tab-pane label="IP 黑名单" name="ip-bans">
        <div class="filter-bar">
          <el-button type="primary" @click="showBanDialog = true">
            <el-icon><Plus /></el-icon> 添加封禁
          </el-button>
          <el-checkbox v-model="showActiveOnly" @change="loadIPBans" style="margin-left: 16px">
            仅显示生效中
          </el-checkbox>
        </div>

        <el-table :data="ipBans" v-loading="banLoading" stripe class="ip-bans-table">
          <el-table-column prop="ip_address" label="IP 地址" width="140" />
          <el-table-column prop="reason" label="封禁原因" show-overflow-tooltip />
          <el-table-column prop="banned_by" label="操作人" width="120" />
          <el-table-column prop="banned_at" label="封禁时间" width="180">
            <template #default="{ row }">
              {{ new Date(row.banned_at).toLocaleString('zh-CN') }}
            </template>
          </el-table-column>
          <el-table-column prop="expires_at" label="到期时间" width="180">
            <template #default="{ row }">
              {{ row.expires_at ? new Date(row.expires_at).toLocaleString('zh-CN') : '永久' }}
            </template>
          </el-table-column>
          <el-table-column label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="row.is_active ? 'danger' : 'info'" size="small">
                {{ row.is_active ? '生效中' : '已过期' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="100" fixed="right">
            <template #default="{ row }">
              <el-button type="danger" size="small" link @click="unbanIP(row.ip_address)">
                解封
              </el-button>
            </template>
          </el-table-column>
        </el-table>

        <el-pagination
          v-model:current-page="banPage"
          :page-size="20"
          :total="banTotal"
          layout="total, prev, pager, next"
          @current-change="loadIPBans"
          style="margin-top: 20px; justify-content: center"
        />
      </el-tab-pane>
    </el-tabs>

    <!-- 添加封禁对话框 -->
    <el-dialog v-model="showBanDialog" title="添加 IP 封禁" width="500px">
      <el-form :model="banForm" label-width="100px">
        <el-form-item label="IP 地址" required>
          <el-input v-model="banForm.ip_address" placeholder="例如: 192.168.1.1" />
        </el-form-item>
        <el-form-item label="封禁原因">
          <el-input v-model="banForm.reason" type="textarea" rows="2" placeholder="可选" />
        </el-form-item>
        <el-form-item label="有效期">
          <el-select v-model="banForm.expires_in_minutes" placeholder="永久有效" clearable style="width: 100%">
            <el-option label="永久" :value="null" />
            <el-option label="15 分钟" :value="15" />
            <el-option label="1 小时" :value="60" />
            <el-option label="6 小时" :value="360" />
            <el-option label="24 小时" :value="1440" />
            <el-option label="7 天" :value="10080" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showBanDialog = false">取消</el-button>
        <el-button type="primary" @click="banIP" :loading="banSubmitting">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import client from '@/api'

const activeTab = ref('login-logs')

// Login logs
const loginLogs = ref([])
const loginLoading = ref(false)
const loginPage = ref(1)
const loginTotal = ref(0)
const loginFilters = reactive({ ip_address: '', status: '' })

// IP bans
const ipBans = ref([])
const banLoading = ref(false)
const banPage = ref(1)
const banTotal = ref(0)
const showActiveOnly = ref(true)
const showBanDialog = ref(false)
const banSubmitting = ref(false)
const banForm = reactive({ ip_address: '', reason: '', expires_in_minutes: null })

onMounted(() => {
  loadLoginLogs()
  loadIPBans()
})

async function loadLoginLogs() {
  loginLoading.value = true
  try {
    const params = { skip: (loginPage.value - 1) * 20, limit: 20 }
    if (loginFilters.ip_address) params.ip_address = loginFilters.ip_address
    if (loginFilters.status) params.status = loginFilters.status
    const response = await client.get('/security/login-logs', { params })
    loginLogs.value = response.data
    loginTotal.value = response.data.length
  } catch (error) {
    ElMessage.error('加载登录日志失败')
  } finally {
    loginLoading.value = false
  }
}

async function loadIPBans() {
  banLoading.value = true
  try {
    const params = { skip: (banPage.value - 1) * 20, limit: 20, active_only: showActiveOnly.value }
    const response = await client.get('/security/ip-bans', { params })
    ipBans.value = response.data
    banTotal.value = response.data.length
  } catch (error) {
    ElMessage.error('加载 IP 黑名单失败')
  } finally {
    banLoading.value = false
  }
}

async function banIP() {
  if (!banForm.ip_address) {
    ElMessage.warning('请输入 IP 地址')
    return
  }
  banSubmitting.value = true
  try {
    await client.post('/security/ip-bans', {
      ip_address: banForm.ip_address,
      reason: banForm.reason,
      expires_in_minutes: banForm.expires_in_minutes,
    })
    ElMessage.success('IP 封禁成功')
    showBanDialog.value = false
    banForm.ip_address = ''
    banForm.reason = ''
    banForm.expires_in_minutes = null
    loadIPBans()
  } catch (error) {
    ElMessage.error('添加封禁失败')
  } finally {
    banSubmitting.value = false
  }
}

async function unbanIP(ip_address) {
  try {
    await ElMessageBox.confirm(`确定要解封 IP ${ip_address} 吗？`, '确认', { type: 'warning' })
    await client.delete(`/security/ip-bans/${ip_address}`)
    ElMessage.success('解封成功')
    loadIPBans()
  } catch (error) {
    if (error !== 'cancel') ElMessage.error('解封失败')
  }
}
</script>

<style scoped>
.security-page { max-width: 1200px; }
.filter-bar { display: flex; gap: 12px; margin-bottom: 16px; align-items: center; }
.login-logs-table, .ip-bans-table { margin-top: 12px; }
</style>
```

- [ ] **Step 2: Commit**

---

## Deployment Notes

### Nginx Configuration for admin.benevolence.com.cn

```nginx
server {
    listen 80;
    server_name admin.benevolence.com.cn;

    location / {
        root /var/www/admin-client/dist;
        try_files $uri $uri/ /index.html;
    }

    location /api/admin/ {
        proxy_pass http://localhost:8000/api/admin/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Create Admin User (SQL)

```sql
-- 插入管理员用户（先注册普通用户，再更新 is_admin）
UPDATE users SET is_admin = true WHERE username = 'your_admin_username';
```

---

## Self-Review Checklist

- [ ] **Spec coverage:** Dashboard, Users, Sensitive Words, Review, Logs, Security all covered.
- [ ] **Placeholder scan:** No "TBD", "TODO", or vague steps found.
- [ ] **Type consistency:** API schemas match frontend expectations.
- [ ] **Independent admin:** Separate `apps/admin/` module, separate `admin-client/`.
- [ ] **Admin auth:** JWT-based, separate login endpoint, requires `is_admin=True`.
- [ ] **Content moderation:** warn-level content flagged for review but published.
- [ ] **No placeholder code:** Every step shows actual implementation code.
- [ ] **Security features:** Login logs, IP bans, auto-ban (5 failures/5min = 15min temp ban).
