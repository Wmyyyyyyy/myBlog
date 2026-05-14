import uuid
from datetime import date, timedelta, datetime
from sqlalchemy import select, func, or_, and_, delete
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import json

from apps.admin.models import AdminLog, LoginLog, IPBan, SecurityLog, AdminOperationLog
from apps.admin.security import verify_password, get_password_hash
from apps.users.models import User
from apps.blogs.models import Blog
from apps.comments.models import Comment
from apps.foundation.models import CheckIn


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


# ==================== New Admin Services ====================


class DashboardService:
    """仪表盘统计服务"""

    async def get_stats(self, db: AsyncSession) -> dict:
        """获取仪表盘统计数据"""
        today = date.today()

        # 基本计数
        user_count_result = await db.execute(select(func.count()).select_from(User))
        user_count = user_count_result.scalar() or 0

        blog_count_result = await db.execute(select(func.count()).select_from(Blog).where(Blog.is_deleted == False))
        blog_count = blog_count_result.scalar() or 0

        comment_count_result = await db.execute(select(func.count()).select_from(Comment).where(Comment.comment_status != 0))
        comment_count = comment_count_result.scalar() or 0

        # 今日活跃用户 (有动态的用户)
        today_start = datetime.combine(today, datetime.min.time())
        dau_result = await db.execute(
            select(func.count(func.distinct(User.id)))
            .select_from(User)
            .join(Blog, Blog.author_id == User.id)
            .where(Blog.created_at >= today_start)
        )
        daily_active_users = dau_result.scalar() or 0

        # 周活跃用户 (7天内)
        week_ago = today - timedelta(days=7)
        week_start = datetime.combine(week_ago, datetime.min.time())
        wau_result = await db.execute(
            select(func.count(func.distinct(User.id)))
            .select_from(User)
            .join(Blog, Blog.author_id == User.id)
            .where(Blog.created_at >= week_start)
        )
        weekly_active_users = wau_result.scalar() or 0

        # 待审核数量 (敏感词标记的内容)
        pending_result = await db.execute(
            select(func.count()).select_from(Blog).where(Blog.status == "pending_review")
        )
        pending_moderation_count = pending_result.scalar() or 0

        # 敏感词触发次数 (最近7天)
        sensitive_trigger_result = await db.execute(
            select(func.count()).select_from(SecurityLog)
            .where(
                SecurityLog.triggered_rule.isnot(None),
                SecurityLog.timestamp >= week_start
            )
        )
        sensitive_word_trigger_count = sensitive_trigger_result.scalar() or 0

        # 今日打卡数
        today_checkin_result = await db.execute(
            select(func.count()).select_from(CheckIn).where(CheckIn.check_in_date == today)
        )
        today_checkin_count = today_checkin_result.scalar() or 0

        return {
            "user_count": user_count,
            "blog_count": blog_count,
            "comment_count": comment_count,
            "daily_active_users": daily_active_users,
            "weekly_active_users": weekly_active_users,
            "pending_moderation_count": pending_moderation_count,
            "sensitive_word_trigger_count": sensitive_word_trigger_count,
            "today_checkin_count": today_checkin_count,
        }


class UserManagementService:
    """用户管理服务"""

    async def list_users(self, db: AsyncSession, keyword: str = None, page: int = 1, page_size: int = 20) -> tuple[list, int]:
        """列出用户，支持关键词搜索和分页"""
        query = select(User)
        count_query = select(func.count()).select_from(User)

        if keyword:
            keyword_filter = or_(
                User.username.ilike(f"%{keyword}%"),
                User.email.ilike(f"%{keyword}%") if hasattr(User, 'email') else False
            )
            query = query.where(keyword_filter)
            count_query = count_query.where(keyword_filter)

        # 获取总数
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # 分页
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size).order_by(User.created_at.desc())
        result = await db.execute(query)
        users = result.scalars().all()

        return list(users), total

    async def get_user(self, db: AsyncSession, user_id: str) -> User:
        """获取单个用户"""
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def update_user(self, db: AsyncSession, user_id: str, data: dict) -> User:
        """更新用户信息"""
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            return None

        for key, value in data.items():
            if hasattr(user, key) and key != 'id':
                setattr(user, key, value)

        await db.flush()
        return user

    async def ban_user(self, db: AsyncSession, user_id: str, reason: str = None) -> None:
        """封禁用户"""
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user:
            user.is_active = False
            await db.flush()

    async def unban_user(self, db: AsyncSession, user_id: str) -> None:
        """解封用户"""
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user:
            user.is_active = True
            await db.flush()

    async def reset_password(self, db: AsyncSession, user_id: str) -> str:
        """重置密码，返回新密码"""
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            return None

        import secrets
        new_password = secrets.token_urlsafe(12)
        user.password_hash = get_password_hash(new_password)
        await db.flush()
        return new_password


class ContentManagementService:
    """内容管理服务"""

    async def list_blogs(self, db: AsyncSession, status: str = None, sensitive_word: str = None, page: int = 1, page_size: int = 20) -> tuple[list, int]:
        """列出博客，支持状态筛选和敏感词筛选"""
        query = select(Blog).where(Blog.is_deleted == False)
        count_query = select(func.count()).select_from(Blog).where(Blog.is_deleted == False)

        if status:
            query = query.where(Blog.status == status)
            count_query = count_query.where(Blog.status == status)

        # 获取总数
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # 分页
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size).order_by(Blog.created_at.desc())
        result = await db.execute(query)
        blogs = result.scalars().all()

        return list(blogs), total

    async def update_blog(self, db: AsyncSession, blog_id: str, data: dict) -> Blog:
        """更新博客"""
        result = await db.execute(select(Blog).where(Blog.id == blog_id))
        blog = result.scalar_one_or_none()
        if not blog:
            return None

        for key, value in data.items():
            if hasattr(blog, key) and key not in ('id', 'author_id'):
                setattr(blog, key, value)

        await db.flush()
        return blog

    async def delete_blog(self, db: AsyncSession, blog_id: str) -> None:
        """删除博客"""
        result = await db.execute(select(Blog).where(Blog.id == blog_id))
        blog = result.scalar_one_or_none()
        if blog:
            blog.is_deleted = True
            await db.flush()

    async def unmark_blog_sensitive(self, db: AsyncSession, blog_id: str) -> None:
        """取消博客敏感标记"""
        result = await db.execute(select(Blog).where(Blog.id == blog_id))
        blog = result.scalar_one_or_none()
        if blog:
            blog.status = "published"
            await db.flush()

    async def list_comments(self, db: AsyncSession, status: str = None, sensitive_word: str = None, page: int = 1, page_size: int = 20) -> tuple[list, int]:
        """列出评论"""
        query = select(Comment).where(Comment.comment_status != 0)  # 不显示已删除
        count_query = select(func.count()).select_from(Comment).where(Comment.comment_status != 0)

        if status:
            query = query.where(Comment.comment_status == int(status))
            count_query = count_query.where(Comment.comment_status == int(status))

        # 获取总数
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # 分页
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size).order_by(Comment.created_at.desc())
        result = await db.execute(query)
        comments = result.scalars().all()

        return list(comments), total

    async def update_comment(self, db: AsyncSession, comment_id: str, data: dict) -> Comment:
        """更新评论"""
        result = await db.execute(select(Comment).where(Comment.id == comment_id))
        comment = result.scalar_one_or_none()
        if not comment:
            return None

        for key, value in data.items():
            if hasattr(comment, key) and key not in ('id', 'author_id', 'blog_id'):
                setattr(comment, key, value)

        await db.flush()
        return comment

    async def delete_comment(self, db: AsyncSession, comment_id: str) -> None:
        """删除评论"""
        result = await db.execute(select(Comment).where(Comment.id == comment_id))
        comment = result.scalar_one_or_none()
        if comment:
            comment.comment_status = 0  # 软删除
            await db.flush()

    async def unmark_comment_sensitive(self, db: AsyncSession, comment_id: str) -> None:
        """取消评论敏感标记"""
        result = await db.execute(select(Comment).where(Comment.id == comment_id))
        comment = result.scalar_one_or_none()
        if comment:
            comment.comment_status = 1  # 恢复正常
            await db.flush()


class SensitiveWordService:
    """敏感词管理服务"""

    # 模拟敏感词数据存储，实际应使用数据库模型
    _words_cache = []

    async def list_words(self, db: AsyncSession, level: int = None, page: int = 1, page_size: int = 50) -> tuple[list, int]:
        """列出敏感词"""
        # 实际实现需要查询数据库
        # 这里返回空列表，实际使用时需要 SensitiveWord 模型
        return [], 0

    async def create_word(self, db: AsyncSession, word: str, level: int, action: str) -> dict:
        """创建敏感词"""
        # 实际实现需要创建 SensitiveWord 记录
        new_word = {
            "id": str(uuid.uuid4()),
            "word": word,
            "level": level,
            "action": action,
            "created_at": datetime.now()
        }
        return new_word

    async def update_word(self, db: AsyncSession, word_id: str, data: dict) -> dict:
        """更新敏感词"""
        # 实际实现需要更新数据库
        return {"id": word_id, **data}

    async def delete_word(self, db: AsyncSession, word_id: str) -> None:
        """删除敏感词"""
        # 实际实现需要从数据库删除
        pass

    async def reload_dfa_tree(self) -> None:
        """触发 Celery 任务重新加载 DFA 树"""
        # 实际实现需要触发 Celery 任务
        # from tasks.moderation import reload_dfa_tree
        # reload_dfa_tree.delay()
        pass


class SecurityLogService:
    """安全日志服务"""

    async def log_security_event(
        self,
        db: AsyncSession,
        ip: str,
        endpoint: str,
        method: str,
        result: str,
        triggered_rule: str = None,
        action_taken: str = 'logged',
        user_id: str = None,
        request_params: dict = None
    ) -> None:
        """记录安全事件"""
        log = SecurityLog(
            ip=ip,
            endpoint=endpoint,
            method=method,
            result=result,
            triggered_rule=triggered_rule,
            action_taken=action_taken,
            user_id=user_id,
            request_params=json.dumps(request_params) if request_params else None,
            timestamp=datetime.now()
        )
        db.add(log)
        await db.flush()

    async def list_logs(
        self,
        db: AsyncSession,
        type: str = None,
        ip: str = None,
        start_date: date = None,
        end_date: date = None,
        page: int = 1,
        page_size: int = 50
    ) -> tuple[list, int]:
        """列出安全日志"""
        query = select(SecurityLog)
        count_query = select(func.count()).select_from(SecurityLog)

        if ip:
            query = query.where(SecurityLog.ip == ip)
            count_query = count_query.where(SecurityLog.ip == ip)

        if type:
            query = query.where(SecurityLog.result == type)
            count_query = count_query.where(SecurityLog.result == type)

        if start_date:
            start_dt = datetime.combine(start_date, datetime.min.time())
            query = query.where(SecurityLog.timestamp >= start_dt)
            count_query = count_query.where(SecurityLog.timestamp >= start_dt)

        if end_date:
            end_dt = datetime.combine(end_date, datetime.max.time())
            query = query.where(SecurityLog.timestamp <= end_dt)
            count_query = count_query.where(SecurityLog.timestamp <= end_dt)

        # 获取总数
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # 分页
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size).order_by(SecurityLog.timestamp.desc())
        result = await db.execute(query)
        logs = result.scalars().all()

        return list(logs), total

    async def export_logs(
        self,
        db: AsyncSession,
        type: str = None,
        start_date: date = None,
        end_date: date = None,
        format: str = 'csv'
    ) -> bytes:
        """导出安全日志"""
        logs, _ = await self.list_logs(db, type, None, start_date, end_date, 1, 100000)

        if format == 'csv':
            import csv
            import io
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(['ID', 'IP', 'Endpoint', 'Method', 'Result', 'Triggered Rule', 'Action Taken', 'Timestamp'])
            for log in logs:
                writer.writerow([
                    log.id,
                    log.ip,
                    log.endpoint,
                    log.method,
                    log.result,
                    log.triggered_rule,
                    log.action_taken,
                    log.timestamp.isoformat() if log.timestamp else ''
                ])
            return output.getvalue().encode('utf-8')

        return b''


class IPBanService:
    """IP封禁服务"""

    async def check_ip_ban(self, db: AsyncSession, ip: str) -> bool:
        """检查 IP 是否被封禁"""
        result = await db.execute(
            select(IPBan).where(
                IPBan.ip_address == ip,
                or_(IPBan.expires_at.is_(None), IPBan.expires_at > datetime.now())
            )
        )
        ban = result.scalar_one_or_none()
        return ban is not None

    async def ban_ip(
        self,
        db: AsyncSession,
        ip: str,
        ban_type: str,
        reason: str = None,
        duration: str = None,
        created_by: str = None
    ) -> IPBan:
        """封禁 IP"""
        # 解析 duration: "24h", "7d", "permanent"
        expires_at = None
        if duration and duration != 'permanent':
            if duration.endswith('h'):
                hours = int(duration[:-1])
                expires_at = datetime.now() + timedelta(hours=hours)
            elif duration.endswith('d'):
                days = int(duration[:-1])
                expires_at = datetime.now() + timedelta(days=days)

        # 检查是否已存在
        result = await db.execute(select(IPBan).where(IPBan.ip_address == ip))
        existing = result.scalar_one_or_none()

        if existing:
            existing.reason = reason
            existing.banned_by = created_by or existing.banned_by
            existing.expires_at = expires_at
            await db.flush()
            return existing

        ban = IPBan(
            ip_address=ip,
            reason=reason,
            banned_by=created_by or "system",
            banned_at=datetime.now(),
            expires_at=expires_at
        )
        db.add(ban)
        await db.flush()
        return ban

    async def unban_ip(self, db: AsyncSession, ip: str) -> None:
        """解封 IP"""
        result = await db.execute(select(IPBan).where(IPBan.ip_address == ip))
        ban = result.scalar_one_or_none()
        if ban:
            await db.delete(ban)
            await db.flush()

    async def unban_all(self, db: AsyncSession, ip: str) -> None:
        """解封该 IP 所有封禁记录"""
        await db.execute(delete(IPBan).where(IPBan.ip_address == ip))
        await db.flush()

    async def list_bans(self, db: AsyncSession, page: int = 1, page_size: int = 50) -> tuple[list, int]:
        """列出封禁记录"""
        query = select(IPBan)
        count_query = select(func.count()).select_from(IPBan)

        # 获取总数
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # 分页
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size).order_by(IPBan.banned_at.desc())
        result = await db.execute(query)
        bans = result.scalars().all()

        return list(bans), total

    async def record_violation(self, db: AsyncSession, ip: str, rule: str) -> int:
        """记录违规次数，返回当前违规计数"""
        # 实际实现可能需要单独的违规记录表
        # 这里简化为记录到安全日志
        log = SecurityLog(
            ip=ip,
            endpoint="violation",
            method="RECORD",
            result="violation_recorded",
            triggered_rule=rule,
            action_taken="count_increment",
            timestamp=datetime.now()
        )
        db.add(log)
        await db.flush()
        return 1  # 实际应返回实际计数

    async def cleanup_expired_bans(self, db: AsyncSession) -> int:
        """清理过期封禁，返回清理数量"""
        result = await db.execute(
            delete(IPBan).where(
                IPBan.expires_at.isnot(None),
                IPBan.expires_at < datetime.now()
            )
        )
        await db.flush()
        return result.rowcount if hasattr(result, 'rowcount') else 0


class OperationLogService:
    """操作日志服务"""

    async def log_operation(
        self,
        db: AsyncSession,
        admin_id: str,
        action: str,
        target_type: str,
        target_id: str = None,
        detail: dict = None,
        ip: str = None
    ) -> None:
        """记录操作日志"""
        log = AdminOperationLog(
            admin_id=admin_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            detail=json.dumps(detail) if detail else None,
            ip=ip,
            created_at=datetime.now()
        )
        db.add(log)
        await db.flush()

    async def list_logs(
        self,
        db: AsyncSession,
        admin_id: str = None,
        action: str = None,
        start_date: date = None,
        end_date: date = None,
        page: int = 1,
        page_size: int = 50
    ) -> tuple[list, int]:
        """列出操作日志"""
        query = select(AdminOperationLog)
        count_query = select(func.count()).select_from(AdminOperationLog)

        if admin_id:
            query = query.where(AdminOperationLog.admin_id == admin_id)
            count_query = count_query.where(AdminOperationLog.admin_id == admin_id)

        if action:
            query = query.where(AdminOperationLog.action.like(f"%{action}%"))
            count_query = count_query.where(AdminOperationLog.action.like(f"%{action}%"))

        if start_date:
            start_dt = datetime.combine(start_date, datetime.min.time())
            query = query.where(AdminOperationLog.created_at >= start_dt)
            count_query = count_query.where(AdminOperationLog.created_at >= start_dt)

        if end_date:
            end_dt = datetime.combine(end_date, datetime.max.time())
            query = query.where(AdminOperationLog.created_at <= end_dt)
            count_query = count_query.where(AdminOperationLog.created_at <= end_date)

        # 获取总数
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # 分页
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size).order_by(AdminOperationLog.created_at.desc())
        result = await db.execute(query)
        logs = result.scalars().all()

        return list(logs), total


class LoginLogService:
    """登录日志服务"""

    async def log_login(
        self,
        db: AsyncSession,
        username: str,
        ip: str,
        user_agent: str = None,
        result: str = 'success',
        fail_reason: str = None,
        user_id: str = None
    ) -> None:
        """记录登录日志"""
        log = LoginLog(
            ip_address=ip,
            user_agent=user_agent,
            login_time=datetime.now(),
            status=result,
            fail_reason=fail_reason,
            admin_id=user_id
        )
        db.add(log)
        await db.flush()

    async def list_logs(
        self,
        db: AsyncSession,
        user_id: str = None,
        result: str = None,
        start_date: date = None,
        end_date: date = None,
        page: int = 1,
        page_size: int = 50
    ) -> tuple[list, int]:
        """列出登录日志"""
        query = select(LoginLog)
        count_query = select(func.count()).select_from(LoginLog)

        if user_id:
            query = query.where(LoginLog.admin_id == user_id)
            count_query = count_query.where(LoginLog.admin_id == user_id)

        if result:
            query = query.where(LoginLog.status == result)
            count_query = count_query.where(LoginLog.status == result)

        if start_date:
            start_dt = datetime.combine(start_date, datetime.min.time())
            query = query.where(LoginLog.login_time >= start_dt)
            count_query = count_query.where(LoginLog.login_time >= start_dt)

        if end_date:
            end_dt = datetime.combine(end_date, datetime.max.time())
            query = query.where(LoginLog.login_time <= end_dt)
            count_query = count_query.where(LoginLog.login_time <= end_dt)

        # 获取总数
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # 分页
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size).order_by(LoginLog.login_time.desc())
        result = await db.execute(query)
        logs = result.scalars().all()

        return list(logs), total
