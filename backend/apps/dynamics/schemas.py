from datetime import datetime
from pydantic import BaseModel
from typing import Optional


class DynamicEventOut(BaseModel):
    id: str
    user_id: str
    event_type: str  # blog_post, like_blog, follow_user
    target_id: Optional[str]
    target_user_id: Optional[str]
    content: Optional[str]
    created_at: datetime

    # 关联的用户信息（需要在 service 中补充）
    username: Optional[str] = None
    user_avatar: Optional[str] = None

    # 扩展字段
    blog_title: Optional[str] = None  # 当 event_type=blog_post 时
    blog_cover: Optional[str] = None  # 当 event_type=blog_post 时

    model_config = {"from_attributes": True}