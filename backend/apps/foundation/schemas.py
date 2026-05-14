from datetime import datetime, date
from pydantic import BaseModel
from typing import Optional


class CheckInResponse(BaseModel):
    id: str
    user_id: str
    check_in_date: date
    streak: int
    achieved_achievements: list[str] = []  # 本次打卡解锁的成就

    model_config = {"from_attributes": True}


class CheckInHistory(BaseModel):
    """用户的打卡历史（分页）"""
    records: list[dict]
    total: int


class CheckInStatus(BaseModel):
    """今日打卡状态"""
    checked_in: bool
    current_streak: int
    longest_streak: int
    total_checkins: int
    check_in_date: Optional[date] = None


class AchievementOut(BaseModel):
    id: str
    achievement_type: str
    achieved_at: datetime

    model_config = {"from_attributes": True}


class AchievementInfo(BaseModel):
    """成就信息（包含是否已解锁）"""
    type: str
    name: str
    description: str
    unlocked: bool
    unlocked_at: Optional[datetime] = None


# 成就定义
ACHIEVEMENTS = {
    "first": {"name": "初次打卡", "description": "完成第一次打卡"},
    "streak_7": {"name": "连续7天", "description": "连续打卡7天"},
    "streak_30": {"name": "连续30天", "description": "连续打卡30天"},
    "streak_100": {"name": "百日筑基", "description": "连续打卡100天"},
}
