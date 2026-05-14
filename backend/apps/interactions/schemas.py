from datetime import datetime
from pydantic import BaseModel
from typing import Optional


class FavoriteResponse(BaseModel):
    id: str
    user_id: str
    blog_id: str
    created_at: datetime

    model_config = {"from_attributes": True}


class LikeResponse(BaseModel):
    id: str
    user_id: str
    blog_id: str
    created_at: datetime

    model_config = {"from_attributes": True}


class FollowResponse(BaseModel):
    id: str
    follower_id: str
    following_id: str
    created_at: datetime

    model_config = {"from_attributes": True}


class MessageResponse(BaseModel):
    message: str