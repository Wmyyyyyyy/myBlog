import pytest
from datetime import date
from apps.foundation.models import CheckIn, Achievement


class TestCheckInModel:
    def test_checkin_create(self):
        checkin = CheckIn(
            user_id="user-uuid",
            check_in_date=date.today(),
            streak=1,
        )
        assert checkin.streak == 1


class TestAchievementModel:
    def test_achievement_create(self):
        achievement = Achievement(
            user_id="user-uuid",
            achievement_type="first",
        )
        assert achievement.achievement_type == "first"
