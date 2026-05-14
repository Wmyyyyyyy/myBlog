from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional


class CommentCreate(BaseModel):
    blog_id: str
    content: str = Field(..., min_length=1, max_length=2000)
    parent_id: Optional[str] = None  # 回复某条评论


class CommentUpdate(BaseModel):
    content: Optional[str] = Field(None, min_length=1, max_length=2000)


class CommentOut(BaseModel):
    id: str
    blog_id: str
    author_id: str
    author_username: str
    content: str
    parent_id: Optional[str]
    root_id: Optional[str]
    level: int
    like_count: int
    reply_count: int
    comment_status: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CommentTreeOut(CommentOut):
    """带嵌套子评论的输出"""
    children: list["CommentTreeOut"] = []
    is_expanded: bool = False  # 是否展开深层回复


class MessageResponse(BaseModel):
    message: str
