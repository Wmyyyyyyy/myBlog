# P5: Foundation（百日筑基）Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Daily check-in system with streak tracking, no makeup days, midnight reset.

**Architecture:**
- CheckIn model: one record per user per day (unique constraint)
- User model: add current_streak, last_check_in_date, longest_streak
- Celery Beat: daily task at 04:00 UTC to check for missed check-ins
- Achievements: NOT implemented (future work)

**Tech Stack:** FastAPI + SQLAlchemy async + PostgreSQL + Redis + Celery Beat + Vue 3 + Pinia

---

## Backend: Foundation Models

### Task 1: Foundation Models & Schemas

**Files:**
- Modify: `backend/apps/foundation/__init__.py`
- Modify: `backend/apps/foundation/models.py` (check existing)
- Create: `backend/apps/foundation/schemas.py`
- Modify: `backend/apps/__init__.py`
- Modify: `backend/apps/users/models.py` (add streak fields)
- Test: `backend/tests/apps/foundation/test_models.py`

- [ ] **Step 1: Check backend/apps/foundation/models.py**

Verify CheckIn model matches design:
```python
class CheckIn(Base):
    __tablename__ = "check_ins"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True)
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    check_in_date: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now())

    __table_args__ = (
        UniqueConstraint('user_id', 'check_in_date', name='uq_user_checkin_date'),
    )
```

- [ ] **Step 2: Add streak fields to User model**

In `backend/apps/users/models.py`, add:
```python
current_streak: Mapped[int] = mapped_column(Integer, default=0)
last_check_in_date: Mapped[date] = mapped_column(Date, nullable=True)
longest_streak: Mapped[int] = mapped_column(Integer, default=0)
```

- [ ] **Step 3: Create backend/apps/foundation/schemas.py**

```python
from datetime import date, datetime
from pydantic import BaseModel
from typing import Optional


class CheckInResponse(BaseModel):
    check_in_date: date
    current_streak: int
    longest_streak: int
    message: str  # "今日已打卡，您已连续 X 天"


class CheckInStatus(BaseModel):
    today_checked_in: bool
    current_streak: int
    longest_streak: int
    message: str


class CheckInHistoryRecord(BaseModel):
    check_in_date: date
    created_at: datetime


class CheckInHistory(BaseModel):
    records: list[CheckInHistoryRecord]
    total: int


class MessageResponse(BaseModel):
    message: str
```

- [ ] **Step 4: Run tests**

```bash
cd backend && .venv/Scripts/python.exe -m pytest tests/apps/foundation/test_models.py -v
```

- [ ] **Step 5: Commit**

---

## Backend: Foundation Services

### Task 2: Foundation Service & Business Logic

**Files:**
- Modify: `backend/apps/foundation/services.py`
- Test: `backend/tests/apps/foundation/test_services.py`

- [ ] **Step 1: Update backend/apps/foundation/services.py**

```python
from datetime import date, datetime, timedelta
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from apps.foundation.models import CheckIn
from apps.users.models import User


class FoundationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def checkin(self, user_id: str) -> dict:
        """每日打卡"""
        today = date.today()
        yesterday = today - timedelta(days=1)

        # 检查今日是否已打卡
        existing = await self.get_checkin_by_date(user_id, today)
        if existing:
            raise ValueError("今日已打卡")

        # 创建打卡记录
        checkin = CheckIn(user_id=user_id, check_in_date=today)
        self.db.add(checkin)

        # 更新用户连续天数
        user = await self.get_user(user_id)
        if not user:
            raise ValueError("User not found")

        if user.last_check_in_date == yesterday:
            # 连续打卡
            user.current_streak += 1
        elif user.last_check_in_date == today:
            # 今日已打卡（理论上不会走到这里）
            pass
        else:
            # 重新开始计数
            user.current_streak = 1

        user.last_check_in_date = today

        # 更新最长连续记录
        if user.current_streak > user.longest_streak:
            user.longest_streak = user.current_streak

        await self.db.flush()

        # 记录动态事件
        from apps.dynamics.services import DynamicService
        dynamic_service = DynamicService(self.db)
        await dynamic_service.record_checkin(user_id, None, None)

        return {
            "check_in_date": today,
            "current_streak": user.current_streak,
            "longest_streak": user.longest_streak,
            "message": f"今日已打卡，您已连续 {user.current_streak} 天"
        }

    async def get_checkin_status(self, user_id: str) -> dict:
        """获取打卡状态"""
        today = date.today()
        user = await self.get_user(user_id)

        today_checked_in = await self.get_checkin_by_date(user_id, today)

        return {
            "today_checked_in": today_checked_in is not None,
            "current_streak": user.current_streak if user else 0,
            "longest_streak": user.longest_streak if user else 0,
            "message": f"今日已打卡，您已连续 {user.current_streak} 天" if today_checked_in
                       else "今日待打卡，开始您的筑基之旅"
        }

    async def get_checkin_history(self, user_id: str, skip: int = 0, limit: int = 20) -> tuple[list, int]:
        """获取打卡历史"""
        # Count total
        count_query = select(func.count(CheckIn.id)).where(CheckIn.user_id == user_id)
        count_result = await self.db.execute(count_query)
        total = count_result.scalar()

        # Get records
        query = select(CheckIn).where(
            CheckIn.user_id == user_id
        ).order_by(CheckIn.check_in_date.desc()).offset(skip).limit(limit)

        result = await self.db.execute(query)
        records = list(result.scalars().all())

        return records, total

    async def get_checkin_by_date(self, user_id: str, check_date: date) -> Optional[CheckIn]:
        query = select(CheckIn).where(
            CheckIn.user_id == user_id,
            CheckIn.check_in_date == check_date
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_user(self, user_id: str) -> Optional[User]:
        from apps.users.models import User
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def reset_missed_checkins(self):
        """重置漏打卡用户的连续天数（Celery 任务调用）"""
        yesterday = date.today() - timedelta(days=1)

        # 查询昨天未打卡且 current_streak > 0 的用户
        query = select(User).where(
            User.last_check_in_date.isnot(None),
            User.last_check_in_date < yesterday,
            User.current_streak > 0
        )
        result = await self.db.execute(query)
        users = result.scalars().all()

        for user in users:
            user.current_streak = 0

        await self.db.flush()
        return len(users)
```

- [ ] **Step 2: Run tests**

```bash
cd backend && .venv/Scripts/python.exe -m pytest tests/apps/foundation/test_services.py -v
```

- [ ] **Step 3: Commit**

---

## Backend: Foundation API Views

### Task 3: Foundation API Views

**Files:**
- Modify: `backend/apps/foundation/router.py`
- Modify: `backend/main.py`
- Test: `backend/tests/apps/foundation/test_router.py`

- [ ] **Step 1: Update backend/apps/foundation/router.py**

```python
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from core.database import get_db
from core.dependencies import get_current_user
from apps.users.models import User
from apps.foundation.schemas import CheckInResponse, CheckInStatus, CheckInHistory, MessageResponse
from apps.foundation.services import FoundationService

router = APIRouter(prefix="/api/foundation", tags=["百日筑基"])


@router.post("/checkin", response_model=CheckInResponse, status_code=status.HTTP_201_CREATED)
async def checkin(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = FoundationService(db)
    try:
        result = await service.checkin(user_id=current_user.id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/status", response_model=CheckInStatus)
async def get_status(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = FoundationService(db)
    result = await service.get_checkin_status(user_id=current_user.id)
    return result


@router.get("/history", response_model=CheckInHistory)
async def get_history(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = FoundationService(db)
    records, total = await service.get_checkin_history(
        user_id=current_user.id,
        skip=skip,
        limit=limit
    )
    return {
        "records": [
            {"check_in_date": r.check_in_date, "created_at": r.created_at}
            for r in records
        ],
        "total": total
    }
```

- [ ] **Step 2: Register router in main.py (if not already registered)**

- [ ] **Step 3: Run tests**

- [ ] **Step 4: Commit**

---

## Backend: Celery Beat Task

### Task 4: Celery Beat Daily Reset Task

**Files:**
- Modify: `backend/tasks/celery_app.py` or `backend/celery_worker.py`
- Create: `backend/tasks/daily_reset.py`

- [ ] **Step 1: Create backend/tasks/daily_reset.py**

```python
from celery import Celery
from datetime import date, timedelta

celery_app = Celery('daily_reset', broker='redis://localhost:6379/0')

@celery_app.task
def reset_missed_checkins():
    """每天 04:00 UTC 检查昨天漏打卡的用户，重置连续天数"""
    from core.database import async_session_maker
    from apps.foundation.services import FoundationService
    import asyncio

    async def _do_reset():
        async with async_session_maker() as session:
            service = FoundationService(session)
            count = await service.reset_missed_checkins()
            return count

    return asyncio.run(_do_reset())
```

- [ ] **Step 2: Configure Celery Beat schedule**

In `celery_app.py` or separate config:
```python
from celery.schedules import crontab

celery_app.conf.beat_schedule = {
    'reset-missed-checkins': {
        'task': 'tasks.daily_reset.reset_missed_checkins',
        'schedule': crontab(hour=4, minute=0),  # 04:00 UTC = 00:00 Beijing
    },
}
```

- [ ] **Step 3: Commit**

---

## Frontend: Foundation UI

### Task 5: Foundation API Client & Store

**Files:**
- Create: `web-client/src/api/foundation.js`
- Create: `web-client/src/stores/foundation.js`

- [ ] **Step 1: Create web-client/src/api/foundation.js**

```javascript
import client from './index'

export const foundationApi = {
  checkin() {
    return client.post('/api/foundation/checkin')
  },
  getStatus() {
    return client.get('/api/foundation/status')
  },
  getHistory(params) {
    return client.get('/api/foundation/history', { params })
  },
}
```

- [ ] **Step 2: Create web-client/src/stores/foundation.js**

```javascript
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { foundationApi } from '@/api/foundation'

export const useFoundationStore = defineStore('foundation', () => {
  const status = ref({
    today_checked_in: false,
    current_streak: 0,
    longest_streak: 0,
    message: ''
  })
  const history = ref([])
  const historyTotal = ref(0)
  const isLoading = ref(false)

  async function fetchStatus() {
    const res = await foundationApi.getStatus()
    status.value = res.data
  }

  async function checkIn() {
    const res = await foundationApi.checkin()
    status.value = res.data
    await fetchHistory()
    return res.data
  }

  async function fetchHistory(params = {}) {
    isLoading.value = true
    try {
      const res = await foundationApi.getHistory(params)
      history.value = res.data.records
      historyTotal.value = res.data.total
    } finally {
      isLoading.value = false
    }
  }

  return {
    status,
    history,
    historyTotal,
    isLoading,
    fetchStatus,
    checkIn,
    fetchHistory,
  }
})
```

- [ ] **Step 3: Commit**

---

### Task 6: Foundation Page Component

**Files:**
- Create: `web-client/src/views/Foundation.vue`
- Modify: `web-client/src/router/index.js`

- [ ] **Step 1: Create web-client/src/views/Foundation.vue**

```vue
<template>
  <div class="foundation-page">
    <div class="header">
      <h1>百日筑基</h1>
      <p class="subtitle">每天进步一点点</p>
    </div>

    <div class="checkin-card">
      <div class="streak-info">
        <div class="streak-item">
          <span class="number">{{ store.status.current_streak }}</span>
          <span class="label">当前连续</span>
        </div>
        <div class="streak-item">
          <span class="number">{{ store.status.longest_streak }}</span>
          <span class="label">历史最长</span>
        </div>
      </div>

      <div class="checkin-status">
        {{ store.status.message }}
      </div>

      <button
        class="checkin-btn"
        :class="{ checked: store.status.today_checked_in }"
        :disabled="store.status.today_checked_in"
        @click="handleCheckin"
      >
        {{ store.status.today_checked_in ? '已打卡' : '立即打卡' }}
      </button>
    </div>

    <div class="history-section">
      <h3>打卡记录</h3>
      <div class="history-list">
        <div v-for="record in store.history" :key="record.check_in_date" class="history-item">
          <span class="date">{{ formatDate(record.check_in_date) }}</span>
          <span class="check-icon">✓</span>
        </div>
        <div v-if="store.history.length === 0" class="empty">
          暂无打卡记录
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useFoundationStore } from '@/stores/foundation'

const store = useFoundationStore()

onMounted(() => {
  store.fetchStatus()
  store.fetchHistory()
})

async function handleCheckin() {
  await store.checkIn()
}

function formatDate(dateStr) {
  return new Date(dateStr).toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
}
</script>

<style scoped>
.foundation-page {
  max-width: 600px;
  margin: 0 auto;
  padding: 24px;
}

.header {
  text-align: center;
  margin-bottom: 32px;
}

.header h1 {
  color: #2d3b30;
  font-size: 28px;
}

.subtitle {
  color: #6b7d72;
  margin-top: 8px;
}

.checkin-card {
  background: #ffffff;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.08);
  text-align: center;
}

.streak-info {
  display: flex;
  justify-content: center;
  gap: 48px;
  margin-bottom: 24px;
}

.streak-item {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.streak-item .number {
  font-size: 48px;
  font-weight: 700;
  color: #5a9672;
}

.streak-item .label {
  font-size: 14px;
  color: #6b7d72;
  margin-top: 4px;
}

.checkin-status {
  color: #2d3b30;
  font-size: 16px;
  margin-bottom: 24px;
}

.checkin-btn {
  width: 100%;
  padding: 16px;
  font-size: 18px;
  font-weight: 600;
  color: white;
  background: #5a9672;
  border: none;
  border-radius: 12px;
  cursor: pointer;
  transition: background 0.2s;
}

.checkin-btn:hover:not(:disabled) {
  background: #4a8562;
}

.checkin-btn:disabled {
  background: #97c9a8;
  cursor: default;
}

.checkin-btn.checked {
  background: #97c9a8;
}

.history-section {
  margin-top: 32px;
}

.history-section h3 {
  color: #2d3b30;
  margin-bottom: 16px;
}

.history-list {
  background: #ffffff;
  border-radius: 16px;
  padding: 16px;
}

.history-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #ddeee5;
}

.history-item:last-child {
  border-bottom: none;
}

.history-item .date {
  color: #2d3b30;
}

.history-item .check-icon {
  color: #5a9672;
  font-weight: bold;
}

.empty {
  text-align: center;
  color: #6b7d72;
  padding: 24px;
}
</style>
```

- [ ] **Step 2: Add route to router**

```javascript
{
  path: '/foundation',
  name: 'Foundation',
  component: () => import('@/views/Foundation.vue'),
  meta: { requiresAuth: true }
}
```

- [ ] **Step 3: Add to navbar**

- [ ] **Step 4: Commit**

---

## Integration Tasks

### Task 7: Update DynamicService for Checkin Events

**Files:**
- Modify: `backend/apps/dynamics/services.py`

- [ ] **Step 1: Add record_checkin method**

Already mentioned in P4 plan. Ensure it's implemented when P5 is built.

- [ ] **Step 2: Commit**

---

## Self-Review Checklist

- [ ] **Spec coverage:** Daily check-in, streak tracking, history, no makeup days.
- [ ] **Celery Beat:** Daily reset task configured.
- [ ] **Message display:** "今日已打卡，您已连续 X 天" / "今日待打卡，开始您的筑基之旅"
- [ ] **No placeholder code:** Every step shows actual implementation code.
- [ ] **Achievements:** NOT implemented (future work, noted in design doc)
