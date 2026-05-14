from datetime import datetime
from pydantic import BaseModel
from typing import Optional


class DynamicEventOut(BaseModel):
    id: str
    event_type: str
    user_id: str
    user_username: str
    user_avatar: Optional[str]
    target_id: Optional[str]
    target_title: Optional[str]
    target_user_id: Optional[str]
    target_user_username: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class FeedResponse(BaseModel):
    events: list[DynamicEventOut]
    next_cursor: Optional[dict] = None  # {"created_at": "...", "id": "..."}


class CursorParams(BaseModel):
    cursor: Optional[str] = None  # URL encoded JSON
    limit: int = 20
