from datetime import date, timedelta
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from apps.foundation.models import CheckIn, Achievement
from apps.foundation.schemas import ACHIEVEMENTS


class FoundationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def check_in(self, user_id: str) -> tuple[CheckIn, list[str]]:
        """
        执行打卡。
        返回：(打卡记录, 本次解锁的成就列表)
        """
        today = date.today()

        # 检查今天是否已打卡
        existing = await self.get_checkin(user_id, today)
        if existing:
            raise ValueError("Already checked in today")

        # 计算连续天数
        yesterday = today - timedelta(days=1)
        yesterday_checkin = await self.get_checkin(user_id, yesterday)

        if yesterday_checkin:
            streak = yesterday_checkin.streak + 1
        else:
            streak = 1  # 断签了，从头开始

        # 创建打卡记录
        checkin = CheckIn(
            user_id=user_id,
            check_in_date=today,
            streak=streak,
        )
        self.db.add(checkin)

        # 检查并解锁成就
        new_achievements = await self.check_achievements(user_id, streak)

        await self.db.flush()
        await self.db.refresh(checkin)
        return checkin, new_achievements

    async def get_checkin(self, user_id: str, check_date: date) -> CheckIn | None:
        result = await self.db.execute(
            select(CheckIn).where(
                CheckIn.user_id == user_id,
                CheckIn.check_in_date == check_date,
            )
        )
        return result.scalar_one_or_none()

    async def get_checkin_history(self, user_id: str) -> dict:
        """获取用户的打卡历史"""
        # 获取所有打卡记录
        result = await self.db.execute(
            select(CheckIn).where(CheckIn.user_id == user_id).order_by(CheckIn.check_in_date.desc())
        )
        checkins = list(result.scalars().all())

        if not checkins:
            return {
                "dates": [],
                "current_streak": 0,
                "longest_streak": 0,
                "total_checkins": 0,
            }

        dates = [c.check_in_date for c in checkins]
        total = len(checkins)

        # 计算当前连续天数
        today = date.today()
        current_streak = 0
        if dates and (today in dates or (today - timedelta(days=1)) in dates):
            # 今天或昨天有打卡
            streak_date = dates[0]
            for c in checkins:
                expected = streak_date + timedelta(days=1)
                if c.check_in_date == expected:
                    current_streak += 1
                    streak_date = c.check_in_date
                else:
                    break
            current_streak += 1  # 加上第一天的

        # 最长连续天数
        longest_streak = max(c.streak for c in checkins) if checkins else 0

        return {
            "dates": dates,
            "current_streak": current_streak,
            "longest_streak": longest_streak,
            "total_checkins": total,
        }

    async def check_achievements(self, user_id: str, current_streak: int) -> list[str]:
        """检查并解锁成就"""
        new_achievements = []

        # 检查各档位成就
        to_check = []
        if current_streak >= 1:
            to_check.append("first")
        if current_streak >= 7:
            to_check.append("streak_7")
        if current_streak >= 30:
            to_check.append("streak_30")
        if current_streak >= 100:
            to_check.append("streak_100")

        for ach_type in to_check:
            # 检查是否已解锁
            result = await self.db.execute(
                select(Achievement).where(
                    Achievement.user_id == user_id,
                    Achievement.achievement_type == ach_type,
                )
            )
            existing = result.scalar_one_or_none()
            if not existing:
                achievement = Achievement(user_id=user_id, achievement_type=ach_type)
                self.db.add(achievement)
                new_achievements.append(ach_type)

        return new_achievements

    async def get_achievements(self, user_id: str) -> list[dict]:
        """获取用户的所有成就"""
        result = await self.db.execute(
            select(Achievement).where(Achievement.user_id == user_id)
        )
        unlocked = {a.achievement_type: a.achieved_at for a in result.scalars().all()}

        return [
            {
                "type": ach_type,
                "name": info["name"],
                "description": info["description"],
                "unlocked": ach_type in unlocked,
                "unlocked_at": unlocked.get(ach_type),
            }
            for ach_type, info in ACHIEVEMENTS.items()
        ]

    async def get_today_status(self, user_id: str) -> dict:
        """获取今天的打卡状态"""
        today = date.today()
        checkin = await self.get_checkin(user_id, today)
        return {
            "checked_in": checkin is not None,
            "streak": checkin.streak if checkin else 0,
        }
