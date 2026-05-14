from datetime import datetime, date
from typing import Optional, Generic, TypeVar
from pydantic import BaseModel, Field


# ==================== Common ====================

T = TypeVar("T")


class PageParams(BaseModel):
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)


class MessageResponse(BaseModel):
    message: str
    code: int = 0


class PageResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int


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
    user_count: int
    blog_count: int
    comment_count: int
    daily_active_users: int
    weekly_active_users: int
    pending_moderation_count: int
    sensitive_word_trigger_count: int
    today_checkin_count: int


# ==================== User Management ====================

class UserListItem(BaseModel):
    id: str
    username: str
    email: Optional[str] = None
    is_active: bool
    is_admin: bool
    created_at: datetime
    blog_count: int
    comment_count: int

    model_config = {"from_attributes": True}


class UserListResponse(BaseModel):
    items: list[UserListItem]
    total: int
    page: int
    page_size: int


class BanUserRequest(BaseModel):
    user_id: str
    reason: Optional[str] = None


class BanUserResponse(BaseModel):
    message: str
    banned_until: Optional[datetime] = None


class ResetPasswordResponse(BaseModel):
    message: str
    new_password: Optional[str] = None


# ==================== Blog Management ====================

class BlogListItem(BaseModel):
    id: str
    title: str
    author_id: str
    author_username: str
    status: str
    created_at: datetime
    comment_count: int
    like_count: int

    model_config = {"from_attributes": True}


class BlogListResponse(BaseModel):
    items: list[BlogListItem]
    total: int
    page: int
    page_size: int


# ==================== Comment Management ====================

class CommentListItem(BaseModel):
    id: str
    content: str
    author_id: str
    author_username: str
    blog_id: str
    blog_title: str
    created_at: datetime

    model_config = {"from_attributes": True}


class CommentListResponse(BaseModel):
    items: list[CommentListItem]
    total: int
    page: int
    page_size: int


# ==================== Sensitive Word Management ====================

class SensitiveWordItem(BaseModel):
    id: str
    word: str
    action: str
    level: Optional[int] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class SensitiveWordListResponse(BaseModel):
    items: list[SensitiveWordItem]
    total: int
    page: int
    page_size: int


class SensitiveWordCreate(BaseModel):
    word: str = Field(..., min_length=1, max_length=50)
    action: str = Field(..., pattern="^(block|replace|warn)$")
    level: Optional[int] = Field(None, ge=1, le=3)


class SensitiveWordUpdate(BaseModel):
    word: Optional[str] = Field(None, min_length=1, max_length=50)
    action: Optional[str] = Field(None, pattern="^(block|replace|warn)$")
    level: Optional[int] = Field(None, ge=1, le=3)


# ==================== Security Logs ====================

class SecurityLogItem(BaseModel):
    id: str
    ip: Optional[str] = None
    timestamp: datetime
    endpoint: Optional[str] = None
    method: Optional[str] = None
    result: Optional[str] = None
    triggered_rule: Optional[str] = None
    action_taken: Optional[str] = None
    user_id: Optional[str] = None
    request_params: Optional[str] = None

    model_config = {"from_attributes": True}


class SecurityLogResponse(BaseModel):
    items: list[SecurityLogItem]
    total: int
    page: int
    page_size: int


# ==================== IP Ban Management ====================

class IPBanItem(BaseModel):
    id: str
    ip: str
    ban_type: str
    reason: Optional[str] = None
    ban_count: int = 0
    expired_at: Optional[datetime] = None
    created_at: datetime
    created_by: Optional[str] = None

    model_config = {"from_attributes": True}


class IPBanListResponse(BaseModel):
    items: list[IPBanItem]
    total: int
    page: int
    page_size: int


class IPBanCreate(BaseModel):
    ip: str
    ban_type: str = Field("permanent", pattern="^(permanent|temporary)$")
    reason: Optional[str] = None
    expires_in_minutes: Optional[int] = None


# ==================== Operation Logs ====================

class OperationLogItem(BaseModel):
    id: str
    admin_id: str
    action: str
    target_type: Optional[str] = None
    target_id: Optional[str] = None
    detail: Optional[str] = None
    ip: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class OperationLogResponse(BaseModel):
    items: list[OperationLogItem]
    total: int
    page: int
    page_size: int


# ==================== Login Logs ====================

class LoginLogItem(BaseModel):
    id: str
    user_id: Optional[str] = None
    username: Optional[str] = None
    ip: Optional[str] = None
    user_agent: Optional[str] = None
    result: str
    fail_reason: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class LoginLogResponse(BaseModel):
    items: list[LoginLogItem]
    total: int
    page: int
    page_size: int


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
