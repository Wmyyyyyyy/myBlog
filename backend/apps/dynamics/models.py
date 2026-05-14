import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Integer, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from core.database import Base


class DynamicEvent(Base):
    """
    用户动态事件（用于动态流展示）
    事件类型：blog_post, like_blog, follow_user
    """
    __tablename__ = "dynamic_events"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)  # blog_post, like_blog, follow_user
    target_id: Mapped[str] = mapped_column(String(100), nullable=True)  # 目标ID（博客ID、用户ID等）
    target_user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=True)  # 关联用户（如被点赞的博客作者）
    content: Mapped[str | None] = mapped_column(Text, nullable=True)  # 动态内容摘要
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(), index=True)