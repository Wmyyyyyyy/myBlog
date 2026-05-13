# 提前准备清单

## 1. 开发环境

### 必需

| 准备项 | 说明 | 验证方式 |
|--------|------|----------|
| Python 3.11+ | FastAPI 需要 | `python --version` |
| Node.js 20+ | Vite/Vue 需要 | `node --version` |
| PostgreSQL 14+ | 本地开发数据库 | 连接测试 |
| Redis 7+ | 缓存 + Celery broker | `redis-cli ping` |
| Git | 版本控制 | `git --version` |

### 推荐

| 准备项 | 说明 | 备注 |
|--------|------|------|
| Docker Desktop | 快速起环境 | 也可用于生产 |
| VS Code | IDE（需装扩展） | Pylance + Volar |
| DataGrip / DBeaver | 数据库管理工具 |  |
| RedisInsight | Redis 可视化 |  |
| Postman / Insomnia | API 测试 |  |

### IDE 扩展推荐

**VS Code 扩展：**
```
Python:
- Pylance
- Python
- Python Debugger

Vue/前端:
- Volar (Vue 3)
- ESLint
- Prettier

其他:
- GitLens
- Thunder Client (API 测试)
```

---

## 2. 账号与密钥

### 必需

| 准备项 | 说明 | 优先级 |
|--------|------|--------|
| 邮件 SMTP 服务 | 发送验证邮件 | 必须（邮箱验证开启时） |
| .env 配置模板 | 提前定义好环境变量 | 必须 |

### 可选

| 准备项 | 说明 | 优先级 |
|--------|------|--------|
| 微信公众平台账号 | 小程序开发 | 预留 |
| 图床/OSS 服务 | 博客图片存储 | 可选（先用本地） |
| 域名 | 部署时需要 | 部署阶段 |
| SSL 证书 | Let's Encrypt | 部署阶段 |

### .env 配置模板

```env
# backend/.env.example

# 应用
APP_NAME=Community Blog
DEBUG=True
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1

# 数据库
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/blog
DATABASE_URL_SYNC=postgresql://user:pass@localhost:5432/blog

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT
JWT_SECRET_KEY=your-jwt-secret
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# 邮件 (开发环境可用 Mailtrap)
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=user@example.com
SMTP_PASSWORD=password
EMAIL_FROM=noreply@example.com
EMAIL_VERIFICATION_ENABLED=False

# Celery
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# 小程序 (预留)
WECHAT_APPID=your-appid
WECHAT_SECRET=your-secret
```

---

## 3. 数据库设计准备

### 必须完成

| 准备项 | 说明 | 交付物 |
|--------|------|--------|
| ER 图设计 | 提前设计好表结构 | 数据库 ER 图 |
| 索引规划 | 避免上线后慢查询 | 索引设计文档 |
| 初始敏感词列表 | 基础审核词库 | 敏感词 JSON 文件 |

### 初始敏感词列表（示例）

```json
[
  "敏感词1",
  "敏感词2",
  "违禁词1",
  "广告内容",
  "诈骗相关",
  "暴力相关",
  "色情相关"
]
```

### 迁移策略

```
开发环境：SQLAlchemy 自动创建表（alembic 后续接入）
生产环境：Alembic 迁移管理
```

---

## 4. 设计资源

### 推荐完成

| 准备项 | 说明 | 优先级 |
|--------|------|--------|
| UI 设计稿 | 确认设计风格和布局 | 推荐 |
| 组件设计规范 | 颜色、字体、间距 | 推荐 |
| API 文档 | Swagger/OpenAPI | 推荐 |

### 设计风格建议

```
整体风格：简洁、现代
主色调：蓝色系或绿色系（可参考现有博客风格）
字体：中文思源黑体/Noto Sans SC + 英文 Inter
布局：响应式（移动端优先）
```

---

## 5. 小程序接口预留

### 提前定义

| 准备项 | 说明 |
|--------|------|
| 统一 API 响应格式 | 与 Web 端一致 |
| 微信授权登录接口 | `/api/auth/wechat` |
| Token 刷新机制 | JWT 续期接口 |
| API 版本管理 | `/api/v1/` |

### 接口契约示例

```typescript
// 小程序端 API 契约

// 微信登录
POST /api/v1/auth/wechat
Request: { code: string }
Response: { token: string, user: UserInfo }

// 刷新 Token
POST /api/v1/auth/refresh
Request: { refresh_token: string }
Response: { token: string }
```

---

## 6. 开发计划里程碑

| 里程碑 | 完成标志 | 建议周期 |
|--------|----------|----------|
| M1: 项目初始化 | 脚手架跑通、CI/CD 就绪、数据库连接正常 | 1 周 |
| M2: 用户+认证 | 注册/登录/JWT 正常、管理后台用户管理 | 1.5 周 |
| M3: 博客+评论 | 博客 CRUD、评论、敏感词审核 | 2 周 |
| M4: 互动+动态 | 收藏/点赞/关注、用户动态流 | 1.5 周 |
| M5: 管理后台 | 完整管理功能、数据统计 | 2 周 |
| M6: 测试+上线 | 自动化测试、部署、优化 | 持续 |

---

## 7. 检查清单

开始开发前请确认：

### 环境
- [ ] Python 3.11+ 已安装
- [ ] Node.js 20+ 已安装
- [ ] PostgreSQL 已安装并运行
- [ ] Redis 已安装并运行
- [ ] Git 仓库已初始化

### 配置
- [ ] .env 文件已创建
- [ ] 数据库连接测试通过
- [ ] Redis 连接测试通过

### 设计
- [ ] 数据库 ER 图已完成
- [ ] 初始敏感词列表已准备
- [ ] API 文档结构已规划

### 文档
- [ ] 开发文档已阅读
- [ ] 测试文档已阅读
- [ ] 项目结构已了解
