import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from core.database import Base


class AdminLog(Base):
    """管理员操作日志"""
    __tablename__ = "admin_logs"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    admin_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    target_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
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
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    fail_reason: Mapped[str | None] = mapped_column(String(200), nullable=True)
    admin_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=True)


class IPBan(Base):
    """IP封禁记录"""
    __tablename__ = "admin_ip_bans"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    ip_address: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    reason: Mapped[str | None] = mapped_column(String(200), nullable=True)
    banned_by: Mapped[str] = mapped_column(String(100), nullable=False)
    banned_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now())
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
