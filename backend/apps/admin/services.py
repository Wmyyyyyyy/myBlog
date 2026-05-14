from datetime import date, timedelta, datetime
from sqlalchemy import select, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from apps.admin.models import AdminLog, LoginLog, IPBan
from apps.admin.security import verify_password
from apps.users.models import User
from apps.blogs.models import Blog
from apps.comments.models import Comment


class AdminAuthService:
    """管理员认证服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def authenticate(self, username: str, password: str) -> Optional[User]:
        result = await self.db.execute(
            select(User).where(User.username == username, User.is_admin == True)
        )
        user = result.scalar_one_or_none()
        if not user:
            return None
        if not verify_password(password, user.password_hash):
            return None
        return user


class AdminDashboardService:
    """Dashboard 统计服务"""

    async def get_stats(self, db: AsyncSession) -> dict:
        today = date.today()

        total_users = await self._count(db, User)
        total_blogs = await self._count(db, Blog)
        total_comments = await self._count(db, Comment)

        from apps.interactions.models import Like, Follow
        total_likes = await self._count(db, Like)
        total_follows = await self._count(db, Follow)

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

    async def ban_user(self, db: AsyncSession, admin_id: str, user_id: str, reason: str = None, ip: str = None) -> bool:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            return False

        user.is_active = False
        await self._log_action(db, admin_id, "ban_user", "user", user_id, reason, ip)
        await db.flush()
        return True

    async def unban_user(self, db: AsyncSession, admin_id: str, user_id: str, ip: str = None) -> bool:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            return False

        user.is_active = True
        await self._log_action(db, admin_id, "unban_user", "user", user_id, ip=ip)
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
        return []

    async def add_word(self, admin_id: str, word: str, action: str) -> dict:
        await self._log_action(self.db, admin_id, "add_sensitive_word", "sensitive_word", word, action)
        return {"word": word, "action": action}

    async def update_word(self, admin_id: str, word_id: str, word: str = None, action: str = None) -> bool:
        await self._log_action(self.db, admin_id, "update_sensitive_word", "sensitive_word", word_id)
        return True

    async def delete_word(self, admin_id: str, word_id: str) -> bool:
        await self._log_action(self.db, admin_id, "delete_sensitive_word", "sensitive_word", word_id)
        return True

    async def reload_filter(self):
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

        if status == "failed":
            await self._check_auto_ban(db, ip_address)

    async def _check_auto_ban(self, db: AsyncSession, ip_address: str) -> None:
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
        result = await db.execute(
            select(IPBan).where(IPBan.ip_address == ip_address)
        )
        existing = result.scalar_one_or_none()

        if existing:
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
