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
    action: str
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
    action: str
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
    status: str
    fail_reason: Optional[str]
    admin_id: Optional[str] = None

    model_config = {"from_attributes": True}


# ==================== Security: IP Bans ====================

class IPBanItem(BaseModel):
    id: str
    ip_address: str
    reason: Optional[str]
    banned_by: str
    banned_at: datetime
    expires_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class CreateIPBan(BaseModel):
    ip_address: str = Field(..., pattern=r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$")
    reason: Optional[str] = None
    expires_in_minutes: Optional[int] = None


class CheckIPResponse(BaseModel):
    is_banned: bool
    reason: Optional[str] = None
    expires_at: Optional[datetime] = None
