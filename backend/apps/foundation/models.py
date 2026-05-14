import uuid
from datetime import datetime, date
from sqlalchemy import String, DateTime, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from core.database import Base


class CheckIn(Base):
    __tablename__ = "check_ins"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False, index=True)
    check_in_date: Mapped[date] = mapped_column(nullable=False, index=True)
    streak: Mapped[int] = mapped_column(Integer, default=1)  # 当天打卡后的连续天数
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now())

    # 唯一约束：每人每天只能打卡一次
    __table_args__ = (
        UniqueConstraint('user_id', 'check_in_date', name='uq_user_checkin_date'),
    )


class Achievement(Base):
    __tablename__ = "achievements"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False, index=True)
    achievement_type: Mapped[str] = mapped_column(String(50), nullable=False)  # "first", "streak_7", "streak_30", "streak_100"
    achieved_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now())

    __table_args__ = (
        UniqueConstraint('user_id', 'achievement_type', name='uq_user_achievement'),
    )
