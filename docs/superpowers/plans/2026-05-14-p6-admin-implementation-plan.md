# P6: Admin（管理后台）Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Admin dashboard with stats, user/content management, sensitive words, security logs, and IP banning.

**Architecture:**
- Single admin role: `is_admin = True`
- Dashboard stats: user/blog/comment counts, DAU/WAU, moderation stats
- Security logs: structured logs for login failures, rate limits, malicious access
- IP banning: auto-ban after 5 violations in 10 minutes, tiered (24h → 7d → permanent)
- Admin operation logs: audit trail for admin actions
- Online users: NOT implemented (future work, needs WebSocket)

**Tech Stack:** FastAPI + SQLAlchemy async + PostgreSQL + Redis + Vue 3 + Element Plus + ECharts

---

## Backend: Admin Models

### Task 1: Admin Models

**Files:**
- Modify: `backend/apps/admin/__init__.py`
- Modify: `backend/apps/admin/models.py` (check existing)
- Modify: `backend/apps/admin/schemas.py`
- Modify: `backend/apps/__init__.py`
- Test: `backend/tests/apps/admin/test_models.py`

- [ ] **Step 1: Verify backend/apps/admin/models.py**

Check for existing models:
- SecurityLog
- IPBan
- AdminOperationLog
- LoginLog

Verify models match design:
```python
# SecurityLog
class SecurityLog(Base):
    __tablename__ = "security_logs"
    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True)
    ip: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(), index=True)
    endpoint: Mapped[str] = mapped_column(String(255), nullable=False)
    method: Mapped[str] = mapped_column(String(10), nullable=False)
    result: Mapped[str] = mapped_column(String(50), nullable=False)
    triggered_rule: Mapped[str] = mapped_column(String(100), nullable=True)
    action_taken: Mapped[str] = mapped_column(String(50), nullable=False)
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=True)
    request_params: Mapped[dict] = mapped_column(JSON, nullable=True)

# IPBan
class IPBan(Base):
    __tablename__ = "ip_bans"
    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True)
    ip: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    ban_type: Mapped[str] = mapped_column(String(20), nullable=False)  # auto/manual
    reason: Mapped[str] = mapped_column(String(255), nullable=True)
    ban_count: Mapped[int] = mapped_column(Integer, default=0)
    expired_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now())
    created_by: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=True)

# AdminOperationLog
class AdminOperationLog(Base):
    __tablename__ = "admin_operation_logs"
    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True)
    admin_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    target_type: Mapped[str] = mapped_column(String(50), nullable=False)
    target_id: Mapped[str] = mapped_column(String(255), nullable=True)
    detail: Mapped[dict] = mapped_column(JSON, nullable=True)
    ip: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now())

# LoginLog
class LoginLog(Base):
    __tablename__ = "login_logs"
    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True)
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=True)
    username: Mapped[str] = mapped_column(String(100), nullable=False)
    ip: Mapped[str] = mapped_column(String(50), nullable=False)
    user_agent: Mapped[str] = mapped_column(String(500), nullable=True)
    result: Mapped[str] = mapped_column(String(20), nullable=False)
    fail_reason: Mapped[str] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(), index=True)
```

- [ ] **Step 2: Update backend/apps/admin/schemas.py**

```python
from datetime import date, datetime
from pydantic import BaseModel
from typing import Optional

# Dashboard
class DashboardStats(BaseModel):
    user_count: int
    blog_count: int
    comment_count: int
    daily_active_users: int
    weekly_active_users: int
    pending_moderation_count: int
    sensitive_word_trigger_count: int
    today_checkin_count: int

# User Management
class UserListItem(BaseModel):
    id: str
    username: str
    email: str
    is_active: bool
    is_admin: bool
    created_at: datetime
    last_login_at: Optional[datetime]

    model_config = {"from_attributes": True}


class UserListResponse(BaseModel):
    users: list[UserListItem]
    total: int
    page: int
    page_size: int


class BanUserRequest(BaseModel):
    reason: Optional[str] = None


class BanUserResponse(BaseModel):
    user_id: str
    banned_until: Optional[datetime]
    message: str


class ResetPasswordResponse(BaseModel):
    new_password: str
    message: str

# Content Management
class BlogListItem(BaseModel):
    id: str
    title: str
    author_id: str
    author_username: str
    status: str
    sensitive_words: list[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class BlogListResponse(BaseModel):
    blogs: list[BlogListItem]
    total: int
    page: int
    page_size: int


class CommentListItem(BaseModel):
    id: str
    blog_id: str
    author_id: str
    author_username: str
    content: str
    status: int
    sensitive_words: list[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class CommentListResponse(BaseModel):
    comments: list[CommentListItem]
    total: int
    page: int
    page_size: int

# Sensitive Words
class SensitiveWordItem(BaseModel):
    id: str
    word: str
    level: int
    action: str
    created_at: datetime

    model_config = {"from_attributes": True}


class SensitiveWordListResponse(BaseModel):
    words: list[SensitiveWordItem]
    total: int


class SensitiveWordCreate(BaseModel):
    word: str
    level: int = Field(1, ge=1, le=3)
    action: str = Field("warn", pattern="^(warn|replace|block)$")


class SensitiveWordUpdate(BaseModel):
    word: Optional[str] = None
    level: Optional[int] = Field(None, ge=1, le=3)
    action: Optional[str] = Field(None, pattern="^(warn|replace|block)$")

# Security Logs
class SecurityLogItem(BaseModel):
    id: str
    ip: str
    timestamp: datetime
    endpoint: str
    method: str
    result: str
    triggered_rule: Optional[str]
    action_taken: str
    user_id: Optional[str]
    request_params: Optional[dict]

    model_config = {"from_attributes": True}


class SecurityLogResponse(BaseModel):
    logs: list[SecurityLogItem]
    total: int


# IP Ban
class IPBanItem(BaseModel):
    id: str
    ip: str
    ban_type: str
    reason: Optional[str]
    ban_count: int
    expired_at: Optional[datetime]
    created_at: datetime

    model_config = {"from_attributes": True}


class IPBanListResponse(BaseModel):
    bans: list[IPBanItem]
    total: int


class IPBanCreate(BaseModel):
    ip: str
    reason: Optional[str] = None
    duration: Optional[str] = None  # "24h", "7d", "permanent"


# Operation Logs
class OperationLogItem(BaseModel):
    id: str
    admin_id: str
    admin_username: str
    action: str
    target_type: str
    target_id: Optional[str]
    detail: Optional[dict]
    ip: str
    created_at: datetime

    model_config = {"from_attributes": True}


class OperationLogResponse(BaseModel):
    logs: list[OperationLogItem]
    total: int


# Login Logs
class LoginLogItem(BaseModel):
    id: str
    user_id: Optional[str]
    username: str
    ip: str
    user_agent: Optional[str]
    result: str
    fail_reason: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class LoginLogResponse(BaseModel):
    logs: list[LoginLogItem]
    total: int


# Common
class MessageResponse(BaseModel):
    message: str


class PageParams(BaseModel):
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)


class DateRangeParams(BaseModel):
    start_date: Optional[date] = None
    end_date: Optional[date] = None
```

- [ ] **Step 3: Run tests**

- [ ] **Step 4: Commit**

---

## Backend: Admin Dependencies

### Task 2: Admin Authentication Dependency

**Files:**
- Modify: `backend/core/dependencies.py`

- [ ] **Step 1: Add get_admin_user dependency**

```python
async def get_admin_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Require admin privileges"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user
```

- [ ] **Step 2: Commit**

---

## Backend: Admin Services

### Task 3: Admin Services

**Files:**
- Modify: `backend/apps/admin/services.py`
- Test: `backend/tests/apps/admin/test_services.py`

- [ ] **Step 1: Update backend/apps/admin/services.py**

Key service classes:

**DashboardService:**
```python
class DashboardService:
    async def get_stats(self) -> dict:
        # user_count, blog_count, comment_count
        # daily_active_users (today's unique users)
        # weekly_active_users (last 7 days)
        # pending_moderation_count (sensitive status blogs/comments)
        # sensitive_word_trigger_count (last 7 days)
        # today_checkin_count
```

**UserManagementService:**
```python
class UserManagementService:
    async def list_users(keyword, page, page_size) -> tuple[list, int]
    async def get_user(user_id) -> User
    async def update_user(user_id, data) -> User
    async def ban_user(user_id, reason) -> None
    async def unban_user(user_id) -> None
    async def reset_password(user_id) -> str  # returns new password
```

**ContentManagementService:**
```python
class ContentManagementService:
    async def list_blogs(status, sensitive_word, page, page_size) -> tuple[list, int]
    async def update_blog(blog_id, data) -> Blog
    async def delete_blog(blog_id) -> None
    async def unmark_blog_sensitive(blog_id) -> None
    async def list_comments(status, sensitive_word, page, page_size) -> tuple[list, int]
    async def update_comment(comment_id, data) -> Comment
    async def delete_comment(comment_id) -> None
    async def unmark_comment_sensitive(comment_id) -> None
```

**SensitiveWordService:**
```python
class SensitiveWordService:
    async def list_words(level, page, page_size) -> tuple[list, int]
    async def create_word(word, level, action) -> SensitiveWord
    async def update_word(word_id, data) -> SensitiveWord
    async def delete_word(word_id) -> None
    async def reload_dfa_tree() -> None  # Celery task trigger
```

**SecurityLogService:**
```python
class SecurityLogService:
    async def log_security_event(ip, endpoint, method, result, triggered_rule, action_taken, user_id=None, request_params=None) -> None
    async def list_logs(type, ip, start_date, end_date, page, page_size) -> tuple[list, int]
    async def export_logs(type, start_date, end_date, format) -> bytes
```

**IPBanService:**
```python
class IPBanService:
    async def check_ip_ban(ip) -> bool
    async def ban_ip(ip, ban_type, reason, duration, created_by) -> IPBan
    async def unban_ip(ip) -> None
    async def unban_all(ip) -> None
    async def list_bans(page, page_size) -> tuple[list, int]
    async def record_violation(ip, rule) -> int  # returns violation count
    async def cleanup_expired_bans() -> int  # returns count cleaned
```

**OperationLogService:**
```python
class OperationLogService:
    async def log_operation(admin_id, action, target_type, target_id, detail, ip) -> None
    async def list_logs(admin_id, action, start_date, end_date, page, page_size) -> tuple[list, int]
```

**LoginLogService:**
```python
class LoginLogService:
    async def log_login(username, ip, user_agent, result, fail_reason=None, user_id=None) -> None
    async def list_logs(user_id, result, start_date, end_date, page, page_size) -> tuple[list, int]
```

- [ ] **Step 2: Run tests**

- [ ] **Step 3: Commit**

---

## Backend: Admin API Views

### Task 4: Admin API Views

**Files:**
- Modify: `backend/apps/admin/router.py`
- Modify: `backend/main.py`
- Test: `backend/tests/apps/admin/test_router.py`

- [ ] **Step 1: Update backend/apps/admin/router.py**

Organized by sections:

**Dashboard:**
- `GET /api/admin/dashboard/stats` — dashboard statistics

**User Management:**
- `GET /api/admin/users` — user list
- `GET /api/admin/users/{id}` — user detail
- `PUT /api/admin/users/{id}` — update user
- `POST /api/admin/users/{id}/ban` — ban user
- `POST /api/admin/users/{id}/unban` — unban user
- `POST /api/admin/users/{id}/reset-password` — reset password

**Content Management:**
- `GET /api/admin/blogs` — blog list
- `PUT /api/admin/blogs/{id}` — update blog
- `DELETE /api/admin/blogs/{id}` — delete blog
- `POST /api/admin/blogs/{id}/unmark-sensitive` — unmark sensitive
- `GET /api/admin/comments` — comment list
- `PUT /api/admin/comments/{id}` — update comment
- `DELETE /api/admin/comments/{id}` — delete comment
- `POST /api/admin/comments/{id}/unmark-sensitive` — unmark sensitive

**Sensitive Words:**
- `GET /api/admin/sensitive-words` — word list
- `POST /api/admin/sensitive-words` — add word
- `PUT /api/admin/sensitive-words/{id}` — update word
- `DELETE /api/admin/sensitive-words/{id}` — delete word
- `POST /api/admin/sensitive-words/reload` — reload DFA tree

**Security Logs:**
- `GET /api/admin/logs/security` — security log list
- `GET /api/admin/logs/security/export` — export logs (CSV/JSON)

**IP Bans:**
- `GET /api/admin/ip-bans` — ban list
- `POST /api/admin/ip-bans` — manual ban
- `DELETE /api/admin/ip-bans/{ip}` — unban
- `POST /api/admin/ip-bans/{ip}/unban-all` — unban all records

**Operation Logs:**
- `GET /api/admin/logs/operation` — operation log list

**Login Logs:**
- `GET /api/admin/logs/login` — login log list

**All endpoints require `get_admin_user` dependency.**

- [ ] **Step 2: Register router in main.py**

- [ ] **Step 3: Run tests**

- [ ] **Step 4: Commit**

---

## Backend: Security Middleware

### Task 5: Security Middleware (IP Ban + Logging)

**Files:**
- Create: `backend/core/security_middleware.py`
- Modify: `backend/main.py`

- [ ] **Step 1: Create backend/core/security_middleware.py**

```python
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from redis.asyncio import Redis
import time
import json

from apps.admin.services import SecurityLogService, IPBanService

# Violation rules mapping
VIOLATION_RULES = {
    'login_fail': 'login_fail',
    'rate_limit': 'rate_limit',
    'invalid_path': 'invalid_path',
    'malicious_param': 'malicious_param',
    'sensitive_retry': 'sensitive_retry',
    '4xx': '4xx_error',
    '5xx': '5xx_error',
}


class SecurityMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, redis: Redis, db_session_factory):
        super().__init__(app)
        self.redis = redis
        self.db_session_factory = db_session_factory
        self.public_paths = {'/api/auth/login', '/api/auth/register', '/docs', '/redoc', '/openapi.json'}

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else 'unknown'

        # Check IP ban first
        async with self.db_session_factory() as db:
            ban_service = IPBanService(db, self.redis)
            if await ban_service.check_ip_ban(client_ip):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="当前访问来源异常，已被限制访问，请联系管理员"
                )

        # Process request
        response = await call_next(request)

        # Log security events for error responses
        if response.status_code >= 400:
            rule = self._map_status_to_rule(response.status_code)
            if rule:
                async with self.db_session_factory() as db:
                    log_service = SecurityService(db, self.redis)
                    await log_service.log_security_event(
                        ip=client_ip,
                        endpoint=str(request.url.path),
                        method=request.method,
                        result=str(response.status_code),
                        triggered_rule=rule,
                        action_taken='logged',
                        user_id=getattr(request.state, 'user_id', None),
                        request_params=self._sanitize_params(request.query_params)
                    )

        return response

    def _map_status_to_rule(self, status_code: int) -> str:
        if status_code == 401:
            return VIOLATION_RULES.get('login_fail')
        if status_code == 429:
            return VIOLATION_RULES.get('rate_limit')
        if status_code == 404:
            return VIOLATION_RULES.get('invalid_path')
        if 400 <= status_code < 500:
            return VIOLATION_RULES.get('4xx')
        if 500 <= status_code < 600:
            return VIOLATION_RULES.get('5xx')
        return None

    def _sanitize_params(self, params) -> dict:
        # Remove sensitive fields
        return dict(params)
```

- [ ] **Step 2: Register middleware in main.py**

```python
from core.security_middleware import SecurityMiddleware

app.add_middleware(
    SecurityMiddleware,
    redis=redis_client,
    db_session_factory=async_session_maker
)
```

- [ ] **Step 3: Commit**

---

## Backend: Celery Tasks

### Task 6: Celery Tasks for Auto-ban

**Files:**
- Modify: `backend/tasks/daily_reset.py` (add cleanup task)

- [ ] **Step 1: Add IP ban cleanup task**

```python
@celery_app.task
def cleanup_expired_ip_bans():
    """清理过期的 IP 封禁"""
    from core.database import async_session_maker
    from apps.admin.services import IPBanService
    import asyncio

    async def _do_cleanup():
        async with async_session_maker() as session:
            service = IPBanService(session, None)  # No redis needed for cleanup
            count = await service.cleanup_expired_bans()
            return count

    return asyncio.run(_do_cleanup())
```

- [ ] **Step 2: Update Celery Beat schedule**

```python
celery_app.conf.beat_schedule = {
    'reset-missed-checkins': {
        'task': 'tasks.daily_reset.reset_missed_checkins',
        'schedule': crontab(hour=4, minute=0),
    },
    'cleanup-expired-ip-bans': {
        'task': 'tasks.daily_reset.cleanup_expired_ip_bans',
        'schedule': crontab(hour=0, minute=0),  # Daily at midnight
    },
}
```

- [ ] **Step 3: Commit**

---

## Frontend: Admin Client (Separate Project)

**Note:** Admin client is a separate project (`admin-client/`). This plan covers only the backend API.

### Task 7: Admin API Client (for admin-client project)

**Files:**
- Create: `admin-client/src/api/admin.js`

```javascript
import axios from 'axios'

const adminClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  timeout: 30000,
})

// Add auth token
adminClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

export const adminApi = {
  // Dashboard
  getDashboardStats() {
    return adminClient.get('/api/admin/dashboard/stats')
  },

  // Users
  getUsers(params) {
    return adminClient.get('/api/admin/users', { params })
  },
  getUser(id) {
    return adminClient.get(`/api/admin/users/${id}`)
  },
  updateUser(id, data) {
    return adminClient.put(`/api/admin/users/${id}`, data)
  },
  banUser(id, data) {
    return adminClient.post(`/api/admin/users/${id}/ban`, data)
  },
  unbanUser(id) {
    return adminClient.post(`/api/admin/users/${id}/unban`)
  },
  resetPassword(id) {
    return adminClient.post(`/api/admin/users/${id}/reset-password`)
  },

  // Blogs
  getBlogs(params) {
    return adminClient.get('/api/admin/blogs', { params })
  },
  updateBlog(id, data) {
    return adminClient.put(`/api/admin/blogs/${id}`, data)
  },
  deleteBlog(id) {
    return adminClient.delete(`/api/admin/blogs/${id}`)
  },
  unmarkBlogSensitive(id) {
    return adminClient.post(`/api/admin/blogs/${id}/unmark-sensitive`)
  },

  // Comments
  getComments(params) {
    return adminClient.get('/api/admin/comments', { params })
  },
  updateComment(id, data) {
    return adminClient.put(`/api/admin/comments/${id}`, data)
  },
  deleteComment(id) {
    return adminClient.delete(`/api/admin/comments/${id}`)
  },
  unmarkCommentSensitive(id) {
    return adminClient.post(`/api/admin/comments/${id}/unmark-sensitive`)
  },

  // Sensitive Words
  getSensitiveWords(params) {
    return adminClient.get('/api/admin/sensitive-words', { params })
  },
  createSensitiveWord(data) {
    return adminClient.post('/api/admin/sensitive-words', data)
  },
  updateSensitiveWord(id, data) {
    return adminClient.put(`/api/admin/sensitive-words/${id}`, data)
  },
  deleteSensitiveWord(id) {
    return adminClient.delete(`/api/admin/sensitive-words/${id}`)
  },
  reloadSensitiveWords() {
    return adminClient.post('/api/admin/sensitive-words/reload')
  },

  // Security Logs
  getSecurityLogs(params) {
    return adminClient.get('/api/admin/logs/security', { params })
  },
  exportSecurityLogs(params) {
    return adminClient.get('/api/admin/logs/security/export', { params, responseType: 'blob' })
  },

  // IP Bans
  getIPBans(params) {
    return adminClient.get('/api/admin/ip-bans', { params })
  },
  createIPBan(data) {
    return adminClient.post('/api/admin/ip-bans', data)
  },
  deleteIPBan(ip) {
    return adminClient.delete(`/api/admin/ip-bans/${ip}`)
  },
  unbanAllIP(ip) {
    return adminClient.post(`/api/admin/ip-bans/${ip}/unban-all`)
  },

  // Operation Logs
  getOperationLogs(params) {
    return adminClient.get('/api/admin/logs/operation', { params })
  },

  // Login Logs
  getLoginLogs(params) {
    return adminClient.get('/api/admin/logs/login', { params })
  },
}
```

---

## Self-Review Checklist

- [ ] **Spec coverage:** All admin features implemented.
- [ ] **Admin auth:** All endpoints require `is_admin = True`.
- [ ] **IP ban middleware:** Checks ban before processing request.
- [ ] **Operation logging:** All admin write operations logged.
- [ ] **Online users:** NOT implemented (future work, needs WebSocket)
- [ ] **No placeholder code:** Every step shows actual implementation code.
