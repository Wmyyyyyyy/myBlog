# P5: Foundation（百日筑基）设计规格书

> **Status:** Draft — 待实现前审核

## 1. 核心规则

### 1.1 打卡机制

- **每日一次**：用户每天只能打卡一次
- **不可补卡**：昨天漏打，今天不能补昨天的卡
- **零点重置**：北京时间 00:00（UTC 04:00）重置打卡状态

### 1.2 文字提醒

打卡状态展示：
- 已打卡：`"今日已打卡，您已连续 X 天"`
- 未打卡：`"今日待打卡，开始您的筑基之旅"`

---

## 2. 数据模型

### 2.1 CheckIn

```python
class CheckIn(Base):
    __tablename__ = "check_ins"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True)
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False, unique=True)  # 每天每个用户一条
    check_in_date: Mapped[date] = mapped_column(Date, nullable=False, unique=True)  # 打卡日期
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now())

    __table_args__ = (
        UniqueConstraint('user_id', 'check_in_date', name='uq_user_checkin_date'),
    )
```

### 2.2 User Streak（用户连续打卡记录）

为了高效查询连续天数，在 User 模型中添加冗余字段：

```python
class User(Base):
    # ... existing fields
    current_streak: Mapped[int] = mapped_column(Integer, default=0)  # 当前连续天数
    last_check_in_date: Mapped[date] = mapped_column(Date, nullable=True)  # 上次打卡日期
    longest_streak: Mapped[int] = mapped_column(Integer, default=0)  # 历史最长连续
```

---

## 3. 打卡逻辑

### 3.1 打卡流程

```
用户点击打卡
    ↓
检查今日是否已打卡 → 已打卡返回错误
    ↓
检查昨天是否打卡 → 未打卡则 streak 重置为 1
    ↓
更新 CheckIn 表
    ↓
更新 User.streak + longest_streak
    ↓
返回打卡结果
```

### 3.2 零点重置逻辑（Celery Beat）

每天 04:00 UTC（北京时间 00:00）执行检查任务：

```python
@celery_app.task
def reset_daily_checkin_status():
    """检查用户是否漏打卡，漏打则重置连续天数"""
    # 查询 last_check_in_date < 昨天的用户
    # 将 current_streak 重置为 0
```

---

## 4. API 设计

| 接口 | 方法 | 说明 | 认证 |
|------|------|------|------|
| `/api/foundation/checkin` | POST | 打卡 | 需要 |
| `/api/foundation/status` | GET | 打卡状态 | 需要 |
| `/api/foundation/history` | GET | 打卡历史（分页） | 需要 |

### 4.1 打卡响应

```json
{
  "code": 0,
  "message": "打卡成功",
  "data": {
    "check_in_date": "2026-05-14",
    "current_streak": 5,
    "longest_streak": 10,
    "message": "今日已打卡，您已连续 5 天"
  }
}
```

### 4.2 状态响应

```json
{
  "code": 0,
  "data": {
    "today_checked_in": true,
    "current_streak": 5,
    "longest_streak": 10,
    "message": "今日已打卡，您已连续 5 天"
  }
}
```

### 4.3 历史响应

```json
{
  "code": 0,
  "data": {
    "records": [
      {"check_in_date": "2026-05-14", "created_at": "2026-05-14T08:00:00Z"},
      {"check_in_date": "2026-05-13", "created_at": "2026-05-13T07:30:00Z"}
    ],
    "total": 30
  }
}
```

---

## 5. 成就系统

**状态**：暂不实现，后续独立开发

**预留字段**（在 User 模型中）：
```python
achievements: Mapped[list[str]] = mapped_column(JSON, default=list)  # ["seven_days", "thirty_days", "hundred_days"]
```

---

## 6. 安全考虑

- 每个用户每天只能打卡一次（数据库唯一约束）
- 打卡接口需要认证
- 零点重置任务需要防止重复执行（Celery 任务幂等性）

---

## 7. 测试场景

1. 用户今日首次打卡：成功，streak +1
2. 用户今日重复打卡：返回错误"今日已打卡"
3. 用户昨天漏打，今天打卡：streak 重置为 1
4. 用户连续打卡 7 天：current_streak = 7，longest_streak 更新
5. 零点重置：漏打用户 streak 重置为 0
