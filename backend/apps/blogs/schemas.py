from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from typing import Optional


class BlogCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)
    excerpt: Optional[str] = Field(None, max_length=500)
    cover_image: Optional[str] = None
    category: Optional[str] = Field(None, max_length=50)
    tags: Optional[str] = None

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Title cannot be empty")
        return v


class BlogUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    content: Optional[str] = Field(None, min_length=1)
    excerpt: Optional[str] = Field(None, max_length=500)
    cover_image: Optional[str] = None
    category: Optional[str] = Field(None, max_length=50)
    tags: Optional[str] = None
    status: Optional[str] = None


class BlogOut(BaseModel):
    id: str
    title: str
    content: str
    excerpt: Optional[str]
    cover_image: Optional[str]
    author_id: str
    category: Optional[str]
    tags: Optional[str]
    status: str
    view_count: int
    like_count: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BlogListOut(BaseModel):
    id: str
    title: str
    excerpt: Optional[str]
    cover_image: Optional[str]
    author_id: str
    author_username: str
    category: Optional[str]
    tags: Optional[str]
    status: str
    view_count: int
    like_count: int
    created_at: datetime

    model_config = {"from_attributes": True}


class ModerationResult(BaseModel):
    passed: bool
    action: str
    original_text: str
    moderated_text: Optional[str] = None
    flagged_words: list[str] = []


class MessageResponse(BaseModel):
    message: str
