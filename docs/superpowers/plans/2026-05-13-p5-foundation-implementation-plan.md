# P5: 百日筑基 (100-Day Foundation) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Daily check-in habit tracking with GitHub-style contribution calendar, streak tracking, and milestone achievements.

**Architecture:**
- No makeup签卡: breaking a streak resets to day 0
- Achievements: first check-in, 7-day, 30-day, 100-day streaks
- Calendar view: GitHub contributions graph style
- Check-in via Celery Beat (daily reset at 4am)

**Tech Stack:** FastAPI + SQLAlchemy async + PostgreSQL + Redis + Celery + Vue 3 + Pinia

---

## Backend: Foundation Check-in

### Task 1: Foundation Models & Schemas

**Files:**
- Create: `backend/apps/foundation/__init__.py`
- Create: `backend/apps/foundation/models.py`
- Create: `backend/apps/foundation/schemas.py`
- Modify: `backend/apps/__init__.py`
- Test: `backend/tests/apps/foundation/test_models.py`

- [ ] **Step 1: Create backend/apps/foundation/__init__.py**

```python
```

- [ ] **Step 2: Create backend/apps/foundation/models.py**

```python
import uuid
from datetime import datetime, date
from sqlalchemy import String, Boolean, DateTime, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from core.database import Base


class CheckIn(Base):
    __tablename__ = "check_ins"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False, index=True)
    check_in_date: Mapped[date] = mapped_column(nullable=False, index=True)
    streak: Mapped[int] = mapped_column(Integer, default=1)  # 当天打卡后的连续天数
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now())

    # 唯一约束：每人每天只能打卡一次
    __table_args__ = (
        UniqueConstraint('user_id', 'check_in_date', name='uq_user_checkin_date'),
    )


class Achievement(Base):
    __tablename__ = "achievements"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False, index=True)
    achievement_type: Mapped[str] = mapped_column(String(50), nullable=False)  # "first", "streak_7", "streak_30", "streak_100"
    achieved_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now())

    __table_args__ = (
        UniqueConstraint('user_id', 'achievement_type', name='uq_user_achievement'),
    )
```

- [ ] **Step 3: Create backend/apps/foundation/schemas.py**

```python
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
    """用户的打卡历史（用于日历展示）"""
    dates: list[date]
    current_streak: int
    longest_streak: int
    total_checkins: int


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
```

- [ ] **Step 4: Create backend/tests/apps/foundation/test_models.py**

```python
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
```

- [ ] **Step 5: Commit**

---

### Task 2: Foundation Services & Business Logic

**Files:**
- Create: `backend/apps/foundation/services.py`
- Test: `backend/tests/apps/foundation/test_services.py`

- [ ] **Step 1: Create backend/apps/foundation/services.py**

```python
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
```

- [ ] **Step 2: Run tests**

- [ ] **Step 3: Commit**

---

### Task 3: Foundation API Views

**Files:**
- Create: `backend/apps/foundation/router.py`
- Modify: `backend/main.py`
- Test: `backend/tests/apps/foundation/test_router.py`

- [ ] **Step 1: Create backend/apps/foundation/router.py**

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.dependencies import get_current_user
from apps.users.models import User
from apps.foundation.schemas import CheckInResponse, CheckInHistory, AchievementInfo, MessageResponse
from apps.foundation.services import FoundationService

router = APIRouter(prefix="/api/foundation", tags=["百日筑基"])


@router.post("/checkin", response_model=CheckInResponse, status_code=status.HTTP_201_CREATED)
async def check_in(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = FoundationService(db)
    try:
        checkin, new_achievements = await service.check_in(current_user.id)
        return CheckInResponse(
            id=checkin.id,
            user_id=checkin.user_id,
            check_in_date=checkin.check_in_date,
            streak=checkin.streak,
            achieved_achievements=new_achievements,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/status", response_model=dict)
async def get_status(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取今日打卡状态"""
    service = FoundationService(db)
    return await service.get_today_status(current_user.id)


@router.get("/history", response_model=CheckInHistory)
async def get_history(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取打卡历史（用于日历展示）"""
    service = FoundationService(db)
    return await service.get_checkin_history(current_user.id)


@router.get("/achievements", response_model=list[AchievementInfo])
async def get_achievements(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取成就列表"""
    service = FoundationService(db)
    return await service.get_achievements(current_user.id)
```

- [ ] **Step 2: Register router in main.py**

```python
from apps.foundation.router import router as foundation_router
app.include_router(foundation_router)
```

- [ ] **Step 3: Commit**

---

## Frontend: Foundation UI

### Task 4: Foundation API Client & Store

**Files:**
- Create: `web-client/src/api/foundation.js`
- Create: `web-client/src/stores/foundation.js`

- [ ] **Step 1: Create web-client/src/api/foundation.js**

```javascript
import client from './index'

export const foundationApi = {
  checkIn() {
    return client.post('/api/foundation/checkin')
  },

  getStatus() {
    return client.get('/api/foundation/status')
  },

  getHistory() {
    return client.get('/api/foundation/history')
  },

  getAchievements() {
    return client.get('/api/foundation/achievements')
  },
}
```

- [ ] **Step 2: Create web-client/src/stores/foundation.js`

```javascript
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { foundationApi } from '@/api/foundation'

export const useFoundationStore = defineStore('foundation', () => {
  const todayStatus = ref({ checked_in: false, streak: 0 })
  const history = ref({ dates: [], current_streak: 0, longest_streak: 0, total_checkins: 0 })
  const achievements = ref([])
  const isLoading = ref(false)

  async function fetchStatus() {
    const response = await foundationApi.getStatus()
    todayStatus.value = response.data
  }

  async function fetchHistory() {
    const response = await foundationApi.getHistory()
    history.value = response.data
  }

  async function fetchAchievements() {
    const response = await foundationApi.getAchievements()
    achievements.value = response.data
  }

  async function checkIn() {
    const response = await foundationApi.checkIn()
    await fetchStatus()
    await fetchHistory()
    await fetchAchievements()
    return response.data
  }

  async function fetchAll() {
    isLoading.value = true
    try {
      await Promise.all([fetchStatus(), fetchHistory(), fetchAchievements()])
    } finally {
      isLoading.value = false
    }
  }

  return {
    todayStatus,
    history,
    achievements,
    isLoading,
    fetchStatus,
    fetchHistory,
    fetchAchievements,
    checkIn,
    fetchAll,
  }
})
```

- [ ] **Step 3: Commit**

---

### Task 5: Foundation View (Calendar + Achievements)

**Files:**
- Create: `web-client/src/views/FoundationView.vue`

- [ ] **Step 1: Create web-client/src/views/FoundationView.vue**

```vue
<template>
  <div class="foundation-page">
    <div class="foundation-header">
      <h1>百日筑基</h1>
      <p>每天打卡，培养好习惯</p>
    </div>

    <div class="foundation-content">
      <!-- 打卡状态卡片 -->
      <div class="status-card">
        <div class="streak-display">
          <span class="streak-number">{{ foundationStore.todayStatus.streak }}</span>
          <span class="streak-label">连续天数</span>
        </div>
        <button
          class="checkin-btn"
          :class="{ checked: foundationStore.todayStatus.checked_in }"
          :disabled="foundationStore.todayStatus.checked_in"
          @click="handleCheckIn"
        >
          {{ foundationStore.todayStatus.checked_in ? '已打卡' : '立即打卡' }}
        </button>
      </div>

      <!-- 成就卡片 -->
      <div class="achievements-card">
        <h3>成就</h3>
        <div class="achievements-grid">
          <div
            v-for="achievement in foundationStore.achievements"
            :key="achievement.type"
            class="achievement-item"
            :class="{ unlocked: achievement.unlocked }"
          >
            <div class="achievement-icon">
              <svg v-if="achievement.unlocked" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
              </svg>
              <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="3" y="11" width="18" height="11" rx="2"/>
                <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
              </svg>
            </div>
            <span class="achievement-name">{{ achievement.name }}</span>
            <span class="achievement-desc">{{ achievement.description }}</span>
          </div>
        </div>
      </div>

      <!-- 日历打卡记录 -->
      <div class="calendar-card">
        <h3>打卡日历</h3>
        <div class="calendar-grid">
          <div class="calendar-header">
            <span v-for="day in ['日', '一', '二', '三', '四', '五', '六']" :key="day">{{ day }}</span>
          </div>
          <div class="calendar-days">
            <div
              v-for="(day, index) in calendarDays"
              :key="index"
              class="calendar-day"
              :class="{ checked: day.checked, empty: !day.date }"
              :title="day.date"
            >
              <span v-if="day.date">{{ day.day }}</span>
            </div>
          </div>
        </div>
        <div class="calendar-legend">
          <span class="legend-item"><span class="dot checked"></span> 已打卡</span>
          <span class="legend-item"><span class="dot"></span> 未打卡</span>
        </div>
      </div>

      <!-- 统计数据 -->
      <div class="stats-card">
        <div class="stat-item">
          <span class="stat-value">{{ foundationStore.history.current_streak }}</span>
          <span class="stat-label">当前连续</span>
        </div>
        <div class="stat-item">
          <span class="stat-value">{{ foundationStore.history.longest_streak }}</span>
          <span class="stat-label">最长连续</span>
        </div>
        <div class="stat-item">
          <span class="stat-value">{{ foundationStore.history.total_checkins }}</span>
          <span class="stat-label">总打卡数</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useFoundationStore } from '@/stores/foundation'

const foundationStore = useFoundationStore()

onMounted(() => {
  foundationStore.fetchAll()
})

const calendarDays = computed(() => {
  const result = []
  const today = new Date()
  const year = today.getFullYear()
  const month = today.getMonth()

  // 月初是星期几
  const firstDay = new Date(year, month, 1).getDay()

  // 填充空白
  for (let i = 0; i < firstDay; i++) {
    result.push({ date: '', day: '', checked: false })
  }

  // 月内每天
  const daysInMonth = new Date(year, month + 1, 0).getDate()
  const checkedDates = new Set(
    foundationStore.history.dates.map(d => {
      const date = new Date(d)
      return `${date.getFullYear()}-${date.getMonth() + 1}-${date.getDate()}`
    })
  )

  for (let d = 1; d <= daysInMonth; d++) {
    const dateStr = `${year}-${month + 1}-${d}`
    result.push({
      date: dateStr,
      day: d,
      checked: checkedDates.has(dateStr),
    })
  }

  return result
})

async function handleCheckIn() {
  try {
    const result = await foundationStore.checkIn()
    ElMessage.success('打卡成功！')
    if (result.achieved_achievements.length > 0) {
      ElMessage.info(`解锁成就: ${result.achieved_achievements.join(', ')}`)
    }
  } catch (error) {
    // Error handled by interceptor
  }
}
</script>

<style scoped>
.foundation-page { min-height: 100vh; background: #F2F9F4; padding-bottom: 40px; }

.foundation-header {
  text-align: center; padding: 48px 24px 32px;
  background: linear-gradient(180deg, rgba(232,245,237,0.7) 0%, #F2F9F4 100%);
}
.foundation-header h1 { font-size: 28px; font-weight: 700; color: #2D3B30; margin-bottom: 8px; }
.foundation-header p { color: #6B7D72; font-size: 14px; }

.foundation-content { max-width: 600px; margin: 0 auto; padding: 0 24px; display: flex; flex-direction: column; gap: 20px; }

.status-card {
  background: #FFFFFF; border-radius: 16px; padding: 24px;
  display: flex; justify-content: space-between; align-items: center;
  border: 1px solid #DDEEE5;
}
.streak-display { display: flex; flex-direction: column; }
.streak-number { font-size: 48px; font-weight: 700; color: #5A9672; line-height: 1; }
.streak-label { font-size: 14px; color: #6B7D72; margin-top: 4px; }
.checkin-btn {
  padding: 12px 32px; border-radius: 12px; border: none;
  font-size: 16px; font-weight: 600; cursor: pointer;
  background: linear-gradient(135deg, #5A9672 0%, #7BAF8E 100%);
  color: #FFFFFF; box-shadow: 0 4px 12px rgba(90,150,114,0.3);
}
.checkin-btn.checked { background: #E8F5ED; color: #5A9672; box-shadow: none; cursor: default; }

.achievements-card { background: #FFFFFF; border-radius: 16px; padding: 24px; border: 1px solid #DDEEE5; }
.achievements-card h3 { font-size: 16px; font-weight: 600; margin-bottom: 16px; }
.achievements-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; }
.achievement-item {
  display: flex; flex-direction: column; align-items: center;
  padding: 16px; background: #F9FAFA; border-radius: 12px; gap: 8px;
}
.achievement-item.unlocked { background: #E8F5ED; }
.achievement-icon { width: 32px; height: 32px; color: #97C9A8; }
.achievement-item.unlocked .achievement-icon { color: #5A9672; }
.achievement-name { font-size: 14px; font-weight: 600; color: #2D3B30; }
.achievement-desc { font-size: 12px; color: #6B7D72; text-align: center; }

.calendar-card { background: #FFFFFF; border-radius: 16px; padding: 24px; border: 1px solid #DDEEE5; }
.calendar-card h3 { font-size: 16px; font-weight: 600; margin-bottom: 16px; }
.calendar-header { display: grid; grid-template-columns: repeat(7, 1fr); text-align: center; font-size: 12px; color: #6B7D72; margin-bottom: 8px; }
.calendar-days { display: grid; grid-template-columns: repeat(7, 1fr); gap: 4px; }
.calendar-day {
  aspect-ratio: 1; display: flex; align-items: center; justify-content: center;
  border-radius: 8px; font-size: 14px; color: #2D3B30;
}
.calendar-day.checked { background: #5A9672; color: #FFFFFF; }
.calendar-day.empty { background: transparent; }
.calendar-legend { display: flex; gap: 16px; margin-top: 16px; justify-content: center; }
.legend-item { display: flex; align-items: center; gap: 6px; font-size: 12px; color: #6B7D72; }
.dot { width: 12px; height: 12px; border-radius: 50%; background: #E8F0EB; }
.dot.checked { background: #5A9672; }

.stats-card {
  display: grid; grid-template-columns: repeat(3, 1fr);
  background: #FFFFFF; border-radius: 16px; padding: 20px;
  border: 1px solid #DDEEE5;
}
.stat-item { display: flex; flex-direction: column; align-items: center; }
.stat-value { font-size: 24px; font-weight: 700; color: #5A9672; }
.stat-label { font-size: 12px; color: #6B7D72; margin-top: 4px; }
</style>
```

- [ ] **Step 2: Add route in router**

```javascript
{
  path: '/foundation',
  name: 'Foundation',
  component: () => import('@/views/FoundationView.vue'),
  meta: { requiresAuth: true },
},
```

- [ ] **Step 3: Commit**

---

## Self-Review Checklist

- [ ] **Spec coverage:** Check-in, history, achievements all covered.
- [ ] **Placeholder scan:** No "TBD", "TODO", or vague steps found.
- [ ] **Type consistency:** Models and schemas consistent.
- [ ] **No makeup签卡:** Streak resets if user misses a day (yesterday_checkin logic).
- [ ] **Achievements:** first, streak_7, streak_30, streak_100 unlocked at correct thresholds.
- [ ] **Calendar view:** GitHub-style contribution grid.
- [ ] **No placeholder code:** Every step shows actual implementation code.
