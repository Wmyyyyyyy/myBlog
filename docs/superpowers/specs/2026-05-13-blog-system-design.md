# 社区博客系统 — 设计规格书

> **Status:** Draft — 待 UI 设计阶段完成后更新

## 1. 项目概述

**项目名称：** 社区博客系统（重构版）
**项目类型：** 全栈 Web 应用
**第一阶段目标：** 用户注册/登录 + JWT 认证

---

## 2. 渐进式开发阶段

| 阶段 | 内容 | 目标 |
|------|------|------|
| **P0** | 项目脚手架 + CI/CD | 可运行的空壳项目，Docker Compose 一键启动 |
| **🖌️ UI 设计** | 设计系统 + 页面布局 + 组件规范 | 设计稿、组件预览页面（设计完成后补充至此文档） |
| **P1** | 用户注册/登录/JWT 认证 | 完整的认证系统 |
| **P2** | 博客 CRUD + 敏感词审核 | 内容发布能力 |
| **P3** | 评论系统 | 用户互动 |
| **P4** | 收藏/点赞/关注 + 动态流 | 社区互动 |
| **P5** | 百日筑基 | 习惯养成功能 |
| **P6** | 管理后台 | 站点管理 |

---

## 3. 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | FastAPI + SQLAlchemy async (asyncpg) |
| 数据库 | PostgreSQL 14+ |
| 缓存/Broker | Redis 7+ |
| 任务队列 | Celery |
| 前端 | Vue 3 (Composition API) + Vite + Pinia + Element Plus + ECharts |
| 管理后台 | Vue 3 + Element Plus + ECharts（独立项目） |
| 部署 | Docker Compose |
| CI/CD | GitHub Actions |

---

## 4. 项目结构

```
myBlog/
├── backend/
│   ├── apps/
│   │   └── users/           # 用户系统（P1）
│   ├── core/
│   │   ├── config.py        # 配置管理
│   │   ├── database.py      # 异步 PostgreSQL
│   │   ├── redis.py         # Redis 连接
│   │   ├── security.py      # JWT/密码加密
│   │   └── dependencies.py  # FastAPI 依赖注入
│   ├── main.py
│   ├── celery_worker.py
│   └── requirements.txt
├── web-client/
│   ├── src/
│   │   ├── api/
│   │   ├── components/
│   │   ├── composables/
│   │   ├── stores/
│   │   ├── views/
│   │   └── router/
│   ├── vite.config.js       # 包含 vite-plugin-openapi
│   └── package.json
├── admin-client/            # 管理后台（独立项目，P6）
│   └── ...
├── docker-compose.yml        # 开发/生产共用
├── docker-compose.prod.yml  # 生产环境补充
└── docs/superpowers/
    ├── specs/               # 设计文档
    └── plans/               # 实施计划
```

---

## 5. API 文档管理方案

### 后端

- FastAPI 原生 OpenAPI schema 自动生成
- 开发环境：`http://localhost:8000/docs`（Swagger UI）
- 备选：`http://localhost:8000/redoc`（ReDoc，更美观）

### 前端

- `vite-plugin-openapi` 插件
- 开发时自动监听 `http://localhost:8000/openapi.json`
- 自动生成 TypeScript 类型 + API 方法到 `src/api/generated/`
- `npm run dev` 时插件自动触发生成（无需手动干预）
- 前端无需维护独立文档，类型即文档

### npm scripts

```json
{
  "scripts": {
    "dev": "vite",
    "build": "vite build"
  }
}
```

---

## 6. 环境与部署设计

### 开发环境（本地）

```
docker-compose.yml
├── postgres (镜像: postgres:15)
├── redis   (镜像: redis:7)
└── backend (本地运行: uvicorn main:app --reload)
```

前端通过 `.env.development` 配置：
```
VITE_API_BASE_URL=http://localhost:8000
```

### 生产环境（Docker Compose）

```
docker-compose.prod.yml
├── nginx        (反向代理 + 静态文件)
├── backend     (uvicorn + workers)
├── postgres    (数据持久化)
└── redis       (缓存持久化)
```

前端构建后由 Nginx 托管，Nginx 配置：
```
location /api/     → proxy_pass 到 backend:8000
location /uploads/ → alias 到 volumes 持久化目录
```

### 配置文件管理

| 文件 | 用途 | 是否入 git |
|------|------|-----------|
| `backend/.env` | 本地后端配置 | 否（加入 .gitignore） |
| `backend/.env.example` | 配置模板 | 是 |
| `web-client/.env.development` | 前端开发配置 | 否 |
| `web-client/.env.production` | 前端生产配置 | 否 |

---

## 7. 管理后台设计

- **独立项目** `admin-client/`，独立 Git 仓库
- **部署域名** `admin.yoursite.com`
- **权限控制**：`is_admin` 布尔标志，无 RBAC
- **技术栈**：同主前端（Vue 3 + Element Plus + ECharts）

---

## 8. P0 脚手架交付物

### 目录结构

- `backend/`：FastAPI 项目框架 + SQLAlchemy async 连接
- `web-client/`：Vue 3 + Vite + Pinia 项目框架
- `docker-compose.yml`：PostgreSQL + Redis
- `.env.example`：所有环境变量模板

### CI/CD

- GitHub Actions：每次 push 运行后端测试 + 前端构建
- Docker Compose 配置用于测试环境

### 数据库

- PostgreSQL 初始化脚本（建表语句在 P1 前暂不执行）
- Redis 本地开发配置

---

## 9. P1 认证系统交付物

### 用户注册/登录

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/auth/register` | POST | 注册（用户名/邮箱/密码） |
| `/api/auth/login` | POST | 登录（返回 JWT） |
| `/api/auth/logout` | POST | 登出 |
| `/api/auth/refresh` | POST | 刷新 Token |
| `/api/auth/me` | GET | 当前用户信息 |

### 功能

- JWT Bearer Token 认证
- HttpOnly Cookie 模式（默认）
- 密码加密（bcrypt）
- 邮箱验证开关（环境变量 `EMAIL_VERIFICATION_ENABLED`）
- 注册时自动创建用户默认头像

### 注册开关

- `EMAIL_VERIFICATION_ENABLED=true`：注册后需邮箱验证才能登录
- `EMAIL_VERIFICATION_ENABLED=false`：注册后直接可登录（开发环境）

---

## 10. 下一步

- P0 脚手架实施（writing-plans skill）
- UI 设计阶段（设计系统 + 页面布局 + 组件规范）
- 设计稿评审 + 更新本设计文档
