import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, Text, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from core.database import Base


class Comment(Base):
    __tablename__ = "comments"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    blog_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("blogs.id"), nullable=False, index=True)
    author_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    parent_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), ForeignKey("comments.id"), nullable=True)
    root_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True, index=True)  # 根评论ID，便于一次拉取所有回复
    level: Mapped[int] = 0  # 0=一级评论, 1=二级, 2=三级
    like_count: Mapped[int] = 0
    reply_count: Mapped[int] = 0
    comment_status: Mapped[int] = 1  # 1=正常, 0=删除, 2=审核中
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(), onupdate=lambda: datetime.now())

    @property
    def is_deleted(self) -> bool:
        return self.comment_status == 0
