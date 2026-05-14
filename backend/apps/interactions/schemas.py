from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional


class FavoriteCreate(BaseModel):
    blog_id: str


class FavoriteOut(BaseModel):
    id: str
    user_id: str
    blog_id: str
    created_at: datetime

    model_config = {"from_attributes": True}


class FavoriteStatus(BaseModel):
    is_favorited: bool
    favorite_count: int


class LikeCreate(BaseModel):
    blog_id: str


class LikeOut(BaseModel):
    id: str
    user_id: str
    blog_id: str
    created_at: datetime

    model_config = {"from_attributes": True}


class LikeStatus(BaseModel):
    is_liked: bool
    like_count: int


class FollowCreate(BaseModel):
    user_id: str  # the user to follow


class FollowOut(BaseModel):
    id: str
    follower_id: str
    following_id: str
    created_at: datetime

    model_config = {"from_attributes": True}


class FollowStatus(BaseModel):
    is_following: bool


class FollowerOut(BaseModel):
    id: str
    username: str
    avatar: Optional[str]
    followed_at: datetime


class FollowingOut(BaseModel):
    id: str
    username: str
    avatar: Optional[str]
    followed_at: datetime


class MessageResponse(BaseModel):
    message: str
