# P6: Admin（管理后台）设计规格书

> **Status:** Draft — 待实现前审核

## 1. 角色与权限

### 1.1 管理员角色

- **单一 admin 角色**：`is_admin = True`
- 无多级权限，管理员拥有全部后台权限
- 普通用户 `is_admin = False`，无法访问后台 API

### 1.2 认证方式

- 使用与普通用户相同的 JWT Token
- Token 中包含 `is_admin` 字段
- 后台 API 统一验证 `is_admin = True`

---

## 2. 仪表盘

### 2.1 统计数据接口

```
GET /api/admin/dashboard/stats
```

**响应**：

```json
{
  "code": 0,
  "data": {
    "user_count": 1000,
    "blog_count": 5000,
    "comment_count": 20000,
    "daily_active_users": 150,
    "weekly_active_users": 500,
    "pending_moderation_count": 15,
    "sensitive_word_trigger_count": 50,
    "today_checkin_count": 80
  }
}
```

**说明**：
- `daily_active_users`：今日有操作的用户数
- `weekly_active_users`：近7天有操作的用户数
- `pending_moderation_count`：待审核内容数
- `sensitive_word_trigger_count`：敏感词触发次数（近7天）

### 2.2 在线用户（后续实现）

```
GET /api/admin/dashboard/online-users
```

**状态**：暂不实现，待 WebSocket 开发完成后实现

---

## 3. 用户管理

### 3.1 用户列表

```
GET /api/admin/users?page=1&page_size=20&keyword=&is_active=
```

**响应**：

```json
{
  "code": 0,
  "data": {
    "users": [
      {
        "id": "uuid",
        "username": "张三",
        "email": "zhangsan@example.com",
        "is_active": true,
        "is_admin": false,
        "created_at": "2026-05-01T10:00:00Z",
        "last_login_at": "2026-05-14T08:00:00Z"
      }
    ],
    "total": 100,
    "page": 1,
    "page_size": 20
  }
}
```

### 3.2 用户操作

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/admin/users/{id}` | GET | 用户详情 |
| `/api/admin/users/{id}` | PUT | 修改用户信息（用户名、邮箱） |
| `/api/admin/users/{id}/ban` | POST | 禁言用户 |
| `/api/admin/users/{id}/unban` | POST | 解禁用户 |
| `/api/admin/users/{id}/reset-password` | POST | 重置密码（发送新密码到邮箱/显示） |

**禁言响应**：

```json
{
  "code": 0,
  "message": "用户已被禁言",
  "data": {
    "user_id": "uuid",
    "banned_until": null  // null 表示永久禁言
  }
}
```

---

## 4. 内容管理

### 4.1 博客列表

```
GET /api/admin/blogs?page=1&page_size=20&status=&sensitive_word=
```

**参数说明**：
- `status`：draft/published/sensitive
- `sensitive_word`：敏感词筛选

### 4.2 评论列表

```
GET /api/admin/comments?page=1&page_size=20&status=&sensitive_word=
```

### 4.3 内容操作

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/admin/blogs/{id}` | PUT | 修改博客（标题、内容、分类） |
| `/api/admin/blogs/{id}` | DELETE | 删除博客 |
| `/api/admin/blogs/{id}/unmark-sensitive` | POST | 解除敏感词标记 |
| `/api/admin/comments/{id}` | PUT | 修改评论 |
| `/api/admin/comments/{id}` | DELETE | 删除评论 |
| `/api/admin/comments/{id}/unmark-sensitive` | POST | 解除敏感词标记 |

---

## 5. 敏感词管理

### 5.1 敏感词列表

```
GET /api/admin/sensitive-words?page=1&page_size=50&level=
```

**响应**：

```json
{
  "code": 0,
  "data": {
    "words": [
      {
        "id": "uuid",
        "word": "敏感词",
        "level": 1,  // 1=warn, 2=replace, 3=block
        "action": "replace",
        "created_at": "2026-05-01T10:00:00Z"
      }
    ],
    "total": 100
  }
}
```

### 5.2 敏感词操作

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/admin/sensitive-words` | POST | 添加敏感词 |
| `/api/admin/sensitive-words/{id}` | PUT | 修改敏感词 |
| `/api/admin/sensitive-words/{id}` | DELETE | 删除敏感词 |
| `/api/admin/sensitive-words/reload` | POST | 重新加载 DFA 树（ Celery 任务） |

---

## 6. 安全日志

### 6.1 日志类型

| 类型 | 说明 | 触发条件 |
|------|------|----------|
| `login_fail` | 登录失败 | 密码错误、用户不存在 |
| `rate_limit` | 接口限流 | 超过限流阈值 |
| `invalid_path` | 非法路径 | 访问不存在的路由 |
| `malicious_param` | 恶意参数 | SQL注入、XSS等 |
| `4xx` | 客户端异常 | 400/401/403/404/422 |
| `5xx` | 服务端异常 | 500/502/503 |

### 6.2 日志数据模型

```python
class SecurityLog(Base):
    __tablename__ = "security_logs"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True)
    ip: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(), index=True)
    endpoint: Mapped[str] = mapped_column(String(255), nullable=False)
    method: Mapped[str] = mapped_column(String(10), nullable=False)
    result: Mapped[str] = mapped_column(String(50), nullable=False)  # success/failed/rate_limited/4xx/5xx
    triggered_rule: Mapped[str] = mapped_column(String(100), nullable=True)
    action_taken: Mapped[str] = mapped_column(String(50), nullable=False)  # logged/blocked/banned
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=True)
    request_params: Mapped[dict] = mapped_column(JSON, nullable=True)
```

### 6.3 日志查询

```
GET /api/admin/logs/security?page=1&page_size=50&type=&ip=&start_date=&end_date=
```

**响应**：

```json
{
  "code": 0,
  "data": {
    "logs": [
      {
        "id": "uuid",
        "ip": "192.168.1.1",
        "timestamp": "2026-05-14T10:00:00Z",
        "endpoint": "/api/auth/login",
        "method": "POST",
        "result": "failed",
        "triggered_rule": "login_fail",
        "action_taken": "logged",
        "user_id": null
      }
    ],
    "total": 1000
  }
}
```

### 6.4 日志导出

```
GET /api/admin/logs/security/export?type=&start_date=&end_date=&format=csv
```

- 支持 CSV/JSON 格式
- 保留 90 天日志（可配置）

---

## 7. IP 封禁

### 7.1 封禁规则

- **自动封禁**：同一 IP，10 分钟内连续 5 次恶意行为
- **恶意行为**：登录失败、越权访问、非法参数、接口恶意刷取、敏感操作重试、4xx/5xx、非法路径试探
- **计数重置**：正常访问后计数清零

### 7.2 封禁数据模型

```python
class IPBan(Base):
    __tablename__ = "ip_bans"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True)
    ip: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    ban_type: Mapped[str] = mapped_column(String(20), nullable=False)  # auto/manual
    reason: Mapped[str] = mapped_column(String(255), nullable=True)
    ban_count: Mapped[int] = mapped_column(Integer, default=0)  # 第几次被封
    expired_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)  # null=永久
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now())
    created_by: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=True)  # 管理员
```

### 7.3 阶梯封禁

| 封禁次数 | 时长 |
|----------|------|
| 第1次 | 24 小时 |
| 第2次 | 7 天 |
| 第3次+ | 永久（需管理员解封） |

### 7.4 封禁检查中间件

```python
# 所有请求先经过 IP 检查
async def check_ip_ban(request: Request):
    if is_ip_banned(request.client.host):
        raise HTTPException(status_code=403, detail="当前访问来源异常，已被限制访问，请联系管理员")
```

### 7.5 封禁管理接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/admin/ip-bans` | GET | 封禁列表 |
| `/api/admin/ip-bans/{ip}` | POST | 手动封禁 IP |
| `/api/admin/ip-bans/{ip}` | DELETE | 解封 IP |
| `/api/admin/ip-bans/{ip}/unban-all` | POST | 解封该 IP 所有封禁记录 |

---

## 8. 操作日志

### 8.1 操作日志模型

```python
class AdminOperationLog(Base):
    __tablename__ = "admin_operation_logs"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True)
    admin_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    action: Mapped[str] = mapped_column(String(100), nullable=False)  # delete_blog/ban_user/update_sensitive_word
    target_type: Mapped[str] = mapped_column(String(50), nullable=False)  # blog/user/sensitive_word
    target_id: Mapped[str] = mapped_column(String(255), nullable=True)
    detail: Mapped[dict] = mapped_column(JSON, nullable=True)  # 操作详情
    ip: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now())
```

### 8.2 操作日志查询

```
GET /api/admin/logs/operation?page=1&page_size=50&admin_id=&action=&start_date=&end_date=
```

---

## 9. 登录日志

### 9.1 登录日志模型

```python
class LoginLog(Base):
    __tablename__ = "login_logs"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True)
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=True)
    username: Mapped[str] = mapped_column(String(100), nullable=False)
    ip: Mapped[str] = mapped_column(String(50), nullable=False)
    user_agent: Mapped[str] = mapped_column(String(500), nullable=True)
    result: Mapped[str] = mapped_column(String(20), nullable=False)  # success/failed
    fail_reason: Mapped[str] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(), index=True)
```

### 9.2 登录日志查询

```
GET /api/admin/logs/login?page=1&page_size=50&user_id=&result=&start_date=&end_date=
```

---

## 10. 安全考虑

- 所有 admin API 需 `is_admin = True` 验证
- 管理员操作记录操作日志（审计）
- IP 封禁在中间件层拦截，不进入业务层
- 敏感操作（如删除、重置密码）记录详细详情
- 日志导出需记录导出操作（防止泄露）
