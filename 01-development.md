# 开发文档

## 1. 项目概述

**项目名称**：社区博客系统（重构版）
**项目类型**：全栈 Web 应用（含小程序扩展预留）
**核心功能**：用户动态、博客发布/管理、评论系统、收藏/点赞/关注、敏感词审核、管理后台、**百日筑基（习惯养成）**
**目标用户**：内容创作者、社区成员、管理员

## 2. 技术栈

| 层级 | 技术 | 用途 |
|------|------|------|
| 后端 | FastAPI | REST API 服务 |
| 数据库 | PostgreSQL | 主数据存储 |
| 缓存 | Redis | 缓存、Celery broker |
| 任务队列 | Celery | 异步任务（邮件、计数等） |
| 前端框架 | Vue 3 (Composition API) | Web 客户端 |
| 构建工具 | Vite | 开发/构建 |
| 状态管理 | Pinia | 前端状态管理 |
| UI 组件库 | Element Plus | 前端组件 |
| 图表库 | ECharts | 数据可视化 |
| 管理后台 | Vue 3 + Element Plus + ECharts | 管理员面板 |
| 小程序 | 微信小程序 | 预留扩展接口 |

## 3. 功能模块

### 3.1 用户系统
- 用户注册/登录（JWT 认证）
- 注册开关控制（管理后台可配置是否需要邮箱验证）
- 用户资料管理

### 3.2 博客模块
- 博客发布/编辑/删除
- 博客列表/详情
- Markdown 编辑器支持
- 敏感词审核（发布前检测）

### 3.3 评论模块
- 评论发布/删除
- 评论列表（支持嵌套）
- 敏感词审核

### 3.4 收藏/点赞/关注
- 博客收藏
- 博客/评论点赞
- 用户关注

### 3.5 用户动态
- 用户行为动态流（发博客、评论、收藏等）
- 动态聚合展示

### 3.6 管理后台
- 用户管理
- 博客管理（审核/删除）
- 评论管理
- 数据统计（ECharts）
- 系统设置（注册验证开关等）

### 3.7 小程序接口预留
- 统一的 API 接口设计
- JWT 认证兼容
- 微信授权登录接口预留

### 3.8 百日筑基（习惯养成）
- 每日打卡（计数器）
- 专注计时器
- 连续打卡天数统计
- 成就系统（7天/30天/100天里程碑）
- 排行榜

## 4. 数据库设计

### 核心表结构

```sql
-- 用户表
users (
  id UUID PRIMARY KEY,
  username VARCHAR(50) UNIQUE NOT NULL,
  email VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  avatar VARCHAR(500),
  bio TEXT,
  is_active BOOLEAN DEFAULT TRUE,
  is_admin BOOLEAN DEFAULT FALSE,
  email_verified BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP,
  updated_at TIMESTAMP
)

-- 博客表
blogs (
  id UUID PRIMARY KEY,
  author_id UUID REFERENCES users(id),
  title VARCHAR(200) NOT NULL,
  content TEXT NOT NULL,
  summary VARCHAR(500),
  cover_image VARCHAR(500),
  category_id UUID REFERENCES categories(id),
  status VARCHAR(20) DEFAULT 'published', -- draft/published/archived
  view_count INTEGER DEFAULT 0,
  like_count INTEGER DEFAULT 0,
  comment_count INTEGER DEFAULT 0,
  is_deleted BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP,
  updated_at TIMESTAMP
)

-- 评论表
comments (
  id UUID PRIMARY KEY,
  blog_id UUID REFERENCES blogs(id),
  author_id UUID REFERENCES users(id),
  parent_id UUID REFERENCES comments(id), -- 嵌套评论
  content TEXT NOT NULL,
  like_count INTEGER DEFAULT 0,
  is_deleted BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP,
  updated_at TIMESTAMP
)

-- 收藏表
collections (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  blog_id UUID REFERENCES blogs(id),
  created_at TIMESTAMP,
  UNIQUE(user_id, blog_id)
)

-- 点赞表
likes (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  target_type VARCHAR(20) NOT NULL, -- blog/comment
  target_id UUID NOT NULL,
  created_at TIMESTAMP,
  UNIQUE(user_id, target_type, target_id)
)

-- 关注表
follows (
  id UUID PRIMARY KEY,
  follower_id UUID REFERENCES users(id),
  following_id UUID REFERENCES users(id),
  created_at TIMESTAMP,
  UNIQUE(follower_id, following_id)
)

-- 用户动态表
dynamics (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  action_type VARCHAR(50) NOT NULL, -- publish_blog/comment/like/collect/follow
  target_type VARCHAR(50),
  target_id UUID,
  metadata JSONB,
  created_at TIMESTAMP
)

-- 敏感词表
sensitive_words (
  id UUID PRIMARY KEY,
  word VARCHAR(100) NOT NULL,
  word_pinyin VARCHAR(200),
  level VARCHAR(20) DEFAULT 'medium', -- low/medium/high/critical
  action VARCHAR(20) DEFAULT 'warn',  -- block/replace/warn
  category_id UUID REFERENCES sensitive_word_categories(id),
  replace_word VARCHAR(100),
  hit_count INTEGER DEFAULT 0,
  false_positive_count INTEGER DEFAULT 0,
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP,
  updated_at TIMESTAMP,
  UNIQUE(word, is_active)
)

-- 敏感词分类表
sensitive_word_categories (
  id UUID PRIMARY KEY,
  name VARCHAR(50) NOT NULL,
  code VARCHAR(20) UNIQUE NOT NULL, -- politics/porn/advert/violence/other
  description TEXT,
  sort_order INTEGER DEFAULT 0
)

-- 审核日志表
moderation_logs (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  content_type VARCHAR(20) NOT NULL, -- blog/comment/dynamic
  content_id UUID,
  content_preview TEXT,
  result VARCHAR(20) NOT NULL,     -- passed/blocked/replaced/warn
  risk_level VARCHAR(20),
  detected_words JSONB,
  created_at TIMESTAMP
)

-- 用户筑基档案
foundation_profiles (
  id UUID PRIMARY KEY,
  user_id UUID UNIQUE REFERENCES users(id),
  started_at DATE,
  total_days INTEGER DEFAULT 0,
  current_streak INTEGER DEFAULT 0,
  longest_streak INTEGER DEFAULT 0,
  total_checkins INTEGER DEFAULT 0,
  total_focus_minutes INTEGER DEFAULT 0,
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP,
  updated_at TIMESTAMP
)

-- 每日打卡记录
foundation_daily (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  date DATE NOT NULL,
  checkin_count INTEGER DEFAULT 0,
  focus_minutes INTEGER DEFAULT 0,
  mood VARCHAR(20),
  note TEXT,
  created_at TIMESTAMP,
  UNIQUE(user_id, date)
)

-- 专注记录（计时器）
foundation_sessions (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  daily_id UUID REFERENCES foundation_daily(id),
  started_at TIMESTAMP NOT NULL,
  ended_at TIMESTAMP,
  duration_minutes INTEGER DEFAULT 0,
  session_type VARCHAR(20) DEFAULT 'focus', -- meditation/focus/exercise
  is_completed BOOLEAN DEFAULT FALSE
)

-- 成就表
achievements (
  id UUID PRIMARY KEY,
  code VARCHAR(50) UNIQUE NOT NULL,
  name VARCHAR(100) NOT NULL,
  description TEXT,
  icon VARCHAR(100),
  requirement JSONB, -- {"type": "streak", "value": 7}
  reward_points INTEGER DEFAULT 0
)

-- 用户成就
user_achievements (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  achievement_id UUID REFERENCES achievements(id),
  earned_at TIMESTAMP,
  UNIQUE(user_id, achievement_id)
)

-- 分类表
categories (
  id UUID PRIMARY KEY,
  name VARCHAR(50) NOT NULL,
  slug VARCHAR(50) UNIQUE,
  description TEXT,
  sort_order INTEGER DEFAULT 0,
  created_at TIMESTAMP
)

-- 系统设置表
system_settings (
  id UUID PRIMARY KEY,
  key VARCHAR(100) UNIQUE NOT NULL,
  value JSONB NOT NULL,
  updated_at TIMESTAMP
)
```

### 索引设计

```sql
CREATE INDEX idx_blogs_author ON blogs(author_id);
CREATE INDEX idx_blogs_status ON blogs(status);
CREATE INDEX idx_blogs_created ON blogs(created_at DESC);
CREATE INDEX idx_comments_blog ON comments(blog_id);
CREATE INDEX idx_comments_parent ON comments(parent_id);
CREATE INDEX idx_likes_target ON likes(target_type, target_id);
CREATE INDEX idx_follows_following ON follows(following_id);
CREATE INDEX idx_follows_follower ON follows(follower_id);
CREATE INDEX idx_dynamics_user ON dynamics(user_id);
CREATE INDEX idx_dynamics_created ON dynamics(created_at DESC);
CREATE INDEX idx_moderation_logs_user ON moderation_logs(user_id);
CREATE INDEX idx_moderation_logs_created ON moderation_logs(created_at DESC);
CREATE INDEX idx_foundation_daily_user ON foundation_daily(user_id);
CREATE INDEX idx_foundation_daily_date ON foundation_daily(date);
CREATE INDEX idx_foundation_sessions_user ON foundation_sessions(user_id);
CREATE INDEX idx_user_achievements_user ON user_achievements(user_id);
```

## 5. API 设计规范

### 响应格式

```json
{
  "code": 0,
  "message": "success",
  "data": { ... }
}
```

错误响应：
```json
{
  "code": 40001,
  "message": "Validation error",
  "errors": { "field": ["error message"] }
}
```

### 认证方式
- JWT Bearer Token
- HttpOnly Cookie 模式（默认）
- 支持小程序端 Token

### 核心接口路径

```
# 认证
POST   /api/auth/register        # 注册
POST   /api/auth/login           # 登录
POST   /api/auth/logout          # 登出
POST   /api/auth/refresh         # 刷新 Token
GET    /api/auth/me              # 当前用户信息

# 博客
GET    /api/blogs                # 博客列表
POST   /api/blogs                # 创建博客
GET    /api/blogs/{id}           # 博客详情
PUT    /api/blogs/{id}           # 更新博客
DELETE /api/blogs/{id}           # 删除博客

# 评论
GET    /api/blogs/{id}/comments  # 获取评论列表
POST   /api/blogs/{id}/comments  # 添加评论
DELETE /api/comments/{id}        # 删除评论

# 收藏/点赞/关注
POST   /api/blogs/{id}/like      # 点赞博客
DELETE /api/blogs/{id}/like      # 取消点赞
POST   /api/blogs/{id}/collect   # 收藏博客
DELETE /api/blogs/{id}/collect   # 取消收藏
POST   /api/users/{id}/follow    # 关注用户
DELETE /api/users/{id}/follow    # 取消关注
GET    /api/users/{id}/followers # 获取粉丝列表
GET    /api/users/{id}/following # 获取关注列表

# 动态
GET    /api/dynamics             # 获取动态流
GET    /api/users/{id}/dynamics  # 获取用户动态

# 分类
GET    /api/categories           # 获取分类列表

# 管理后台
GET    /api/admin/users          # 用户列表
PUT    /api/admin/users/{id}     # 更新用户
DELETE /api/admin/users/{id}     # 删除用户
GET    /api/admin/blogs          # 博客列表（全部）
DELETE /api/admin/blogs/{id}     # 删除博客
GET    /api/admin/comments       # 评论列表
DELETE /api/admin/comments/{id}  # 删除评论
GET    /api/admin/stats          # 统计数据
GET    /api/admin/sensitive-words           # 敏感词列表
POST   /api/admin/sensitive-words           # 添加敏感词
DELETE /api/admin/sensitive-words/{id}      # 删除敏感词
GET    /api/admin/settings       # 获取系统设置
PUT    /api/admin/settings       # 更新系统设置

# 百日筑基
GET    /api/foundation/profile          # 获取我的筑基档案
POST   /api/foundation/checkin         # 打卡
POST   /api/foundation/sessions        # 开始专注时段
PUT    /api/foundation/sessions/{id}   # 结束专注时段
GET    /api/foundation/stats            # 统计
GET    /api/foundation/leaderboard      # 排行榜
GET    /api/foundation/achievements    # 我的成就
POST   /api/foundation/achievements/{id}/claim  # 领取成就
```

## 6. API 文档管理

### 6.1 后端：Swagger/OpenAPI 自动文档

FastAPI 自带 Swagger UI，代码即文档，改接口后自动更新。

```python
# main.py
from fastapi import FastAPI

app = FastAPI(
    title="社区博客 API",
    version="1.0.0",
    description="Vue + FastAPI 博客系统",
    docs_url="/docs",        # Swagger UI
    redoc_url="/redoc",      # ReDoc（更美观）
    openapi_url="/openapi.json",  # 供前端使用
)
```

访问地址：
| 环境 | 地址 |
|------|------|
| 开发 | `http://localhost:8000/docs` |
| 预发布 | `https://api.pre.yourdomain.com/docs` |
| 生产 | `https://api.yourdomain.com/docs` |

### 6.2 前端：自动生成 API 类型

使用 `openapi-typescript-codegen` 根据后端 Schema 自动生成 TypeScript 类型。

```bash
npm install openapi-typescript-codegen -D
```

```javascript
// scripts/generate-api.js
const OpenAPI = require('openapi-typescript-codegen')

OpenAPI.generate({
  input: 'http://localhost:8000/openapi.json',
  output: './src/api/generated',
  client: 'axios',
  exportSchemas: true,
})
```

```json
// package.json
{
  "scripts": {
    "generate:api": "node scripts/generate-api.js",
    "dev": "npm run generate:api && vite",
    "build": "npm run generate:api && vite build"
  }
}
```

**生成的文件示例：**

```typescript
// src/api/generated/index.ts

export interface Blog {
  id: string
  title: string
  content: string
  author: User
  like_count: number
  comment_count: number
  created_at: string
}

export interface User {
  id: string
  username: string
  avatar: Avatar
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

// 自动生成的 API 方法
export class BlogsService {
  static async createBlog(data: CreateBlogRequest): Promise<Blog>
  static async getBlog(id: string): Promise<Blog>
  static async listBlogs(params?: ListBlogsParams): Promise<PaginatedResponse<Blog>>
  static async updateBlog(id: string, data: UpdateBlogRequest): Promise<Blog>
  static async deleteBlog(id: string): Promise<void>
}
```

### 6.3 开发时自动同步

**方式 1：Vite 插件**

```typescript
// vite.config.ts
import { defineConfig } from 'vite'
import ApiPlugin from 'vite-plugin-openapi'

export default defineConfig({
  plugins: [
    ApiPlugin({
      target: 'http://localhost:8000',
      output: './src/api/generated',
      watch: true,         // 监听变化自动重新生成
      client: 'axios',
    })
  ]
})
```

**方式 2：concurrently 同时启动**

```bash
npm install concurrently -D
```

```json
{
  "scripts": {
    "dev:all": "concurrently \"npm run dev:backend\" \"npm run dev:frontend\"",
    "dev:backend": "cd backend && uvicorn main:app --reload",
    "dev:frontend": "vite",
    "generate:api": "node scripts/generate-api.js"
  }
}
```

### 6.4 开发流程

```
1. 启动后端  →  FastAPI 自动生成 openapi.json
                                      │
2. 启动前端  →  插件自动下载 schema
                    │
3. 生成 TypeScript 类型 + API 方法
                    │
4. 前端开发时调用生成的 API
                    │
5. 修改后端接口  →  重启后端  →  前端自动重新生成
```

### 6.5 文档工具对比

| 工具 | 用途 | 特点 |
|------|------|------|
| **Swagger UI** (`/docs`) | 后端在线文档 | 代码即文档，完全自动 |
| **ReDoc** (`/redoc`) | 更美观的文档 | 侧边栏导航，适合对外展示 |
| **openapi-typescript-codegen** | 前端类型生成 | 消除前后端类型不一致 |
| ** scalar** | 现代 API 文档 | 界面美观，支持 Mock |

### 6.6 API 文档输出格式

```yaml
# openapi.yaml (导出给第三方)
openapi: 3.0.0
info:
  title: 社区博客 API
  version: 1.0.0
paths:
  /api/blogs:
    get:
      summary: 获取博客列表
      tags: [博客]
      parameters:
        - name: page
          in: query
          schema:
            type: integer
            default: 1
        - name: page_size
          in: query
          schema:
            type: integer
            default: 10
      responses:
        '200':
          description: 成功
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PaginatedBlogs'
```

## 7. 项目结构

```
backend/
├── apps/
│   ├── __init__.py
│   ├── users/              # 用户系统
│   │   ├── __init__.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── views.py
│   │   ├── services.py
│   │   └── tests/
│   ├── blogs/              # 博客模块
│   │   ├── __init__.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── views.py
│   │   ├── services.py
│   │   └── tests/
│   ├── comments/           # 评论模块
│   │   ├── __init__.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── views.py
│   │   ├── services.py
│   │   └── tests/
│   ├── interactions/        # 收藏/点赞/关注
│   │   ├── __init__.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── views.py
│   │   ├── services.py
│   │   └── tests/
│   ├── dynamics/            # 用户动态
│   │   ├── __init__.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── views.py
│   │   ├── services.py
│   │   └── tests/
│   ├── moderation/          # 敏感词审核
│   │   ├── __init__.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── views.py
│   │   ├── services.py      # DFA 敏感词检测服务
│   │   └── tests/
│   ├── foundation/           # 百日筑基
│   │   ├── __init__.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── views.py
│   │   ├── services.py
│   │   └── tests/
│   └── upload/              # 图片上传
│       ├── __init__.py
│       ├── views.py
│       ├── schemas.py
│       └── tests/
└── admin/              # 管理后台 API
    ├── __init__.py
    ├── views.py
    ├── schemas.py
    └── tests/
├── core/
│   ├── __init__.py
│   ├── config.py           # 配置管理
│   ├── database.py         # 数据库连接
│   ├── redis.py           # Redis 连接
│   ├── security.py         # JWT/密码加密
│   ├── dependencies.py     # FastAPI 依赖注入
│   ├── exceptions.py       # 自定义异常
│   ├── storage.py          # 存储接口（本地/OSS）
│   └── image.py            # 图片处理工具
├── tasks/                   # Celery 任务
│   ├── __init__.py
│   ├── email.py
│   └── counter.py
├── tests/
│   ├── conftest.py
│   └── apps/
├── requirements.txt
├── main.py                  # FastAPI 入口
└── celery_worker.py         # Celery 入口

web-client/
├── src/
│   ├── api/                # API 调用封装
│   │   ├── index.js
│   │   ├── auth.js
│   │   ├── blog.js
│   │   ├── comment.js
│   │   └── user.js
│   ├── components/         # 公共组件
│   │   ├── blog/
│   │   ├── comment/
│   │   ├── common/
│   │   └── user/
│   ├── composables/       # 组合式函数
│   │   ├── useAuth.js
│   │   ├── useBlog.js
│   │   └── useComment.js
│   ├── stores/            # Pinia stores
│   │   ├── auth.js
│   │   ├── blog.js
│   │   └── user.js
│   ├── views/             # 页面组件
│   │   ├── Home.vue
│   │   ├── BlogDetail.vue
│   │   ├── BlogEditor.vue
│   │   ├── UserProfile.vue
│   │   └── Foundation.vue  # 百日筑基页面
│   ├── stores/            # Pinia stores
│   │   ├── auth.js
│   │   ├── blog.js
│   │   ├── user.js
│   │   └── foundation.js  # 筑基状态
│   ├── router/
│   │   └── index.js
│   ├── styles/
│   │   └── index.scss
│   ├── utils/
│   │   └── index.js
│   ├── App.vue
│   └── main.js
├── tests/
│   ├── components/
│   ├── composables/
│   └── e2e/
├── package.json
└── vite.config.js

admin-client/                # 管理后台前端
├── src/
│   ├── api/
│   ├── components/
│   ├── views/
│   │   ├── dashboard/
│   │   ├── user/
│   │   ├── blog/
│   │   ├── comment/
│   │   └── settings/
│   ├── stores/
│   └── router/
├── tests/
└── package.json

miniprogram/                 # 小程序（预留）
├── src/
└── package.json
```

## 8. 敏感词审核设计（DFA 算法）

### 7.1 方案对比

| 方案 | 算法复杂度 | 优点 | 缺点 | 推荐度 |
|------|-----------|------|------|--------|
| **DFA** | O(n) 查找 | 性能最优、内存占用低、支持变体 | 建树有初始开销 | ⭐⭐⭐⭐⭐ |
| AC自动机 | O(n) 多模式 | 批量匹配效率高 | 内存占用大、实现复杂 | ⭐⭐⭐ |
| 正则匹配 | O(n*m) | 简单灵活 | 性能差、无法处理变体 | ⭐⭐ |

### 7.2 审核流程

```
用户提交内容
     │
     ▼
文本标准化（繁→简、全角→半角、大写→小写）
     │
     ▼
DFA 树匹配（O(n)，毫秒级）
     │
     ├── 无敏感词 → 通过
     │
     └── 有敏感词
           ├── action=block → 直接拒绝（HTTP 400）
           ├── action=replace → 自动替换为 **** 后通过
           └── action=warn → 返回警告，用户可选择强制发布
```

### 7.3 DFA 算法实现

```python
# sensitive_word/service.py
from typing import List, Dict, Tuple, Optional
import json
import threading
import redis

class DFANode:
    """DFA 树节点"""
    def __init__(self):
        self.children: Dict[str, DFANode] = {}
        self.is_end: bool = False
        self.word: Optional[str] = None
        self.level: str = "medium"      # low/medium/high/critical
        self.action: str = "warn"       # block/replace/warn

class DFATree:
    """DFA 树"""
    def __init__(self):
        self.root = DFANode()
        self._lock = threading.RLock()

    def add_word(self, word: str, level: str = "medium", action: str = "warn"):
        with self._lock:
            node = self.root
            for char in word.lower():
                if char not in node.children:
                    node.children[char] = DFANode()
                node = node.children[char]
            node.is_end = True
            node.word = word
            node.level = level
            node.action = action

    def find(self, text: str) -> List[Dict]:
        """查找所有敏感词"""
        results = []
        text_len = len(text)

        i = 0
        while i < text_len:
            node = self.root
            j = i
            last_match = None

            while j < text_len:
                char = text[j].lower()
                if char not in node.children:
                    break
                node = node.children[char]
                if node.is_end:
                    last_match = {"word": node.word, "level": node.level, "action": node.action}
                j += 1

            if last_match:
                results.append(last_match)
                i = j
            else:
                i += 1

        return results

class SensitiveWordService:
    """敏感词检测服务"""
    CACHE_KEY = "sensitive:dfa_tree"
    WHITELIST_KEY = "sensitive:whitelist"

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self._dfa_tree: Optional[DFATree] = None
        self._whitelist: set = set()
        self._lock = threading.RLock()

    def _build_tree(self) -> DFATree:
        """从数据库构建 DFA 树"""
        from models import SensitiveWord
        tree = DFATree()
        words = SensitiveWord.objects.filter(is_active=True)
        for word in words:
            tree.add_word(word.word, word.level, word.action)
        return tree

    def _ensure_tree(self) -> DFATree:
        """确保 DFA 树已加载"""
        if self._dfa_tree:
            return self._dfa_tree
        with self._lock:
            # 尝试从 Redis 缓存读取
            cached = self.redis.get(self.CACHE_KEY)
            if cached:
                tree_data = json.loads(cached)
                self._dfa_tree = self._deserialize_tree(tree_data)
            else:
                self._dfa_tree = self._build_tree()
                self.redis.set(self.CACHE_KEY, json.dumps(self._serialize_tree(self._dfa_tree)))
            return self._dfa_tree

    def check(self, text: str) -> Tuple[bool, List[Dict]]:
        """检测敏感词，返回 (是否通过, 敏感词列表)"""
        if not text:
            return True, []

        tree = self._ensure_tree()
        normalized = self._normalize(text)  # 繁简/全角/大小写转换
        results = tree.find(normalized)

        # 过滤白名单
        results = [r for r in results if r["word"] not in self._whitelist]
        return len(results) == 0, results

    def _normalize(self, text: str) -> str:
        """文本标准化"""
        # 繁→简
        char_map = {"台": "臺", "国": "國", "学": "學", ...}
        for k, v in char_map.items():
            text = text.replace(k, v)
        # 全角→半角
        # ...
        return text.lower()

    def reload(self):
        """热更新：管理后台修改敏感词后调用"""
        with self._lock:
            self._dfa_tree = self._build_tree()
            self.redis.delete(self.CACHE_KEY)

    def check_and_action(self, text: str) -> Dict:
        """检测并返回处理建议"""
        passed, words = self.check(text)
        if passed:
            return {"passed": True, "action": "allow"}

        # 聚合最高风险等级
        level_priority = {"low": 1, "medium": 2, "high": 3, "critical": 4}
        max_level = max(words, key=lambda w: level_priority.get(w["level"], 0))["level"]

        if any(w["action"] == "block" for w in words):
            return {"passed": False, "action": "block", "level": max_level, "words": words}
        elif any(w["action"] == "replace" for w in words):
            return {"passed": True, "action": "replace", "level": max_level, "words": words}
        else:
            return {"passed": True, "action": "warn", "level": max_level, "words": words}
```

### 7.4 敏感词 API

```python
# moderation/views.py
@router.post("/blogs")
async def create_blog(data: BlogCreate, user: User = Depends(get_current_user)):
    # 敏感词检测
    result = sensitive_word_service.check_and_action(data.content)

    if not result["passed"]:
        raise HTTPException(status_code=400, detail=result["message"])

    if result["action"] == "replace":
        # 自动替换敏感词
        data.content = sensitive_word_service.replace(data.content)

    blog = await BlogService.create(data, user)

    # 记录审核日志
    await ModerationLog.create(
        user_id=user.id,
        content_type="blog",
        content_id=blog.id,
        result=result["action"],
        risk_level=result.get("level"),
        detected_words=result.get("words", [])
    )

    return blog
```

## 9. Celery 异步任务架构

### 8.1 为什么需要 Celery

| 场景 | 不用 Celery | 用 Celery |
|------|------------|----------|
| 发送邮件 | HTTP 请求阻塞 2-5s | 用户立即收到响应，邮件后台发送 |
| 更新点赞计数 | 高并发下数据库压力大 | 异步批量合并，减轻数据库压力 |
| 生成报表 | 请求超时 | 后台任务，完成后通知 |
| 敏感词热更新 | 重启服务 | 定时任务自动刷新缓存 |

### 8.2 架构图

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  FastAPI    │────▶│   Redis     │────▶│  Celery     │
│  (HTTP)     │     │  (Broker)  │     │  (Worker)   │
└─────────────┘     └─────────────┘     └─────────────┘
                                            │
                                            ▼
                                      ┌─────────────┐
                                      │  PostgreSQL  │
                                      │  (结果存储)  │
                                      └─────────────┘
```

### 8.3 核心任务实现

```python
# tasks/email.py
from celery import Celery
celery_app = Celery("tasks", broker="redis://localhost:6379/0")

@celery_app.task
def send_verification_email(email: str, code: str):
    """发送邮箱验证码"""
    # 调用邮件服务（sendgrid/mailgun）
    send_email(to=email, subject="验证码", body=f"您的验证码: {code}")
    return {"sent": True}

# tasks/counter.py
@celery_app.task
def sync_like_count(content_type: str, content_id: str, delta: int):
    """批量同步点赞数到数据库"""
    sql = f"""
    UPDATE {content_type}s
    SET like_count = like_count + {delta}
    WHERE id = '{content_id}'
    """
    db.execute(sql)

@celery_app.task
def flush_pending_like_counts():
    """将 Redis 缓存的点赞数批量写入数据库（每5分钟）"""
    pending = redis.smembers("pending:likes")
    # 批量更新...
```

### 8.4 Celery Beat 定时任务

```python
# celery_config.py
from celery.schedules import crontab

app.conf.beat_schedule = {
    # 每5分钟：合并点赞计数到数据库
    "sync-like-counts": {
        "task": "tasks.counter.sync_like_counts",
        "schedule": 300.0,
    },
    # 每小时：清理过期缓存
    "cleanup-expired": {
        "task": "tasks.cache.cleanup_expired",
        "schedule": 3600.0,
    },
    # 每天凌晨3点：生成统计数据
    "daily-stats": {
        "task": "tasks.stats.generate_daily",
        "schedule": crontab(hour=3, minute=0),
    },
    # 每天凌晨4点：重置"百日筑基"每日数据
    "reset-daily-checkin": {
        "task": "tasks.foundation.reset_daily",
        "schedule": crontab(hour=4, minute=0),
    },
    # 每天凌晨2点：重载敏感词 DFA 树
    "reload-sensitive-words": {
        "task": "tasks.moderation.reload_dfa_tree",
        "schedule": crontab(hour=2, minute=0),
    },
}
```

## 10. 百日筑基功能详解

### 9.1 功能概述

"百日筑基"是一个习惯养成/自律打卡系统，融合计数器与计时器。

| 模块 | 功能 |
|------|------|
| **计数器** | 每日打卡次数、连续打卡天数、最长连续记录 |
| **计时器** | 专注时长、每日目标达成、累计修行时间 |
| **排行榜** | 连续天数榜、累计时长榜 |
| **成就系统** | 7天/30天/100天里程碑成就 |

### 9.2 核心业务逻辑

```python
# foundation/services.py
from datetime import datetime, date, timedelta
from typing import Optional

class FoundationService:
    DAILY_GOAL_MINUTES = 30  # 默认每日目标30分钟

    async def checkin(self, user_id: UUID, note: str = None) -> dict:
        """打卡"""
        today = date.today()

        # 获取或创建今日记录
        daily, created = await FoundationDaily.get_or_create(
            user_id=user_id, date=today,
            defaults={"checkin_count": 0, "focus_minutes": 0}
        )
        daily.checkin_count += 1
        await daily.save()

        # 更新档案
        profile = await FoundationProfile.get(user_id)
        profile.total_checkins += 1

        # 计算连续天数
        if profile.last_checkin_date == today - timedelta(days=1):
            profile.current_streak += 1
        elif profile.last_checkin_date != today:
            profile.current_streak = 1

        profile.last_checkin_date = today
        profile.longest_streak = max(profile.longest_streak, profile.current_streak)
        await profile.save()

        # 检查成就
        achievements = await self._check_achievements(user_id, profile)

        return {
            "streak": profile.current_streak,
            "checkin_count": daily.checkin_count,
            "achievements": achievements
        }

    async def start_session(self, user_id: UUID, session_type: str = "focus") -> dict:
        """开始专注时段"""
        session = FoundationSession(
            user_id=user_id,
            started_at=datetime.now(),
            session_type=session_type
        )
        # 写入 Redis（实时状态）
        await redis.set(f"foundation:session:{user_id}", session.model_dump_json())
        return {"session_id": session.id, "started_at": session.started_at}

    async def end_session(self, user_id: UUID, session_id: UUID) -> dict:
        """结束专注时段"""
        session_data = await redis.get(f"foundation:session:{user_id}")
        session = json.loads(session_data)

        ended_at = datetime.now()
        duration = (ended_at - session["started_at"]).seconds // 60

        # 更新数据库
        today = date.today()
        daily = await FoundationDaily.get(user_id, today)
        daily.focus_minutes += duration
        await daily.save()

        # 更新档案累计
        profile = await FoundationProfile.get(user_id)
        profile.total_focus_minutes += duration
        await profile.save()

        # 删除 Redis 状态
        await redis.delete(f"foundation:session:{user_id}")

        return {
            "duration": duration,
            "goal_met": daily.focus_minutes >= self.DAILY_GOAL_MINUTES,
            "total_today": daily.focus_minutes
        }

    async def _check_achievements(self, user_id: UUID, profile: FoundationProfile) -> list:
        """检查并发放成就"""
        earned = []
        all_achievements = await Achievement.get_all()

        for ach in all_achievements:
            req = ach.requirement
            if req["type"] == "streak" and profile.current_streak >= req["value"]:
                if not await UserAchievement.exists(user_id, ach.id):
                    await UserAchievement.create(user_id=user_id, achievement_id=ach.id)
                    earned.append(ach)

        return earned
```

### 9.3 前端组件

```vue
<!-- FoundationCard.vue -->
<template>
  <div class="foundation-card zen-card">
    <div class="streak-badge">
      <span class="days">{{ profile.current_streak }}</span>
      <span class="label">连续天数</span>
    </div>

    <div class="today-progress">
      <div class="progress-ring">
        <svg viewBox="0 0 100 100">
          <circle cx="50" cy="50" r="45" stroke="#eee" stroke-width="8" fill="none"/>
          <circle cx="50" cy="50" r="45" stroke="#4CAF50" stroke-width="8" fill="none"
            :stroke-dasharray="`${progress * 2.83} 283`"
            transform="rotate(-90 50 50)"/>
        </svg>
        <span class="minutes">{{ todayMinutes }} / {{ dailyGoal }} 分钟</span>
      </div>
    </div>

    <div class="actions">
      <button @click="checkin" class="checkin-btn">打卡</button>
      <button @click="startTimer" class="timer-btn">开始计时</button>
    </div>
  </div>
</template>

<style scoped>
.foundation-card {
  padding: 20px;
  text-align: center;
}
.streak-badge .days {
  font-size: 48px;
  font-weight: bold;
  color: #4CAF50;
}
.progress-ring circle:last-child {
  transition: stroke-dasharray 0.5s;
}
</style>
```

## 12. 图片上传与存储

### 11.1 存储方案对比

| 方案 | 优点 | 缺点 | 推荐场景 |
|------|------|------|----------|
| **本地存储 + 预留 OSS** | 简单、无需第三方、初期成本低 | 难以扩展、无 CDN | **当前推荐** |
| **云 OSS（阿里云/腾讯云）** | CDN 加速、无限扩容、流量费用低 | 需要第三方服务、有存储费用 | 未来迁移目标 |

**架构设计：本地优先，预留 OSS 扩展接口**

```
本地存储（当前）
┌─────────────────────────────────────────────┐
│  /uploads/                                 │
│    ├── avatars/{user_id}/                  │
│    │   ├── sm.webp (48px)                 │
│    │   ├── md.webp (128px)                │
│    │   └── lg.webp (256px)                │
│    └── blogs/{blog_id}/                    │
│        ├── original.webp (原图)            │
│        ├── compressed.webp (2000px)        │
│        ├── thumbnail.webp (400px)          │
│        └── mobile.webp (1080px)            │
└─────────────────────────────────────────────┘
        ↓ 未来扩展
 OSS Storage 实现类（只需替换工厂类）
```

### 11.2 存储接口设计（策略模式）

```python
# core/storage.py
from abc import ABC, abstractmethod
from typing import Dict
import asyncio

class BaseStorage(ABC):
    """存储抽象基类，预留 OSS 扩展"""
    @abstractmethod
    async def upload(self, key: str, data: bytes, content_type: str) -> str: pass

    @abstractmethod
    async def upload_multiple(self, files: Dict[str, bytes], prefix: str) -> Dict[str, str]: pass

    @abstractmethod
    async def delete(self, key: str) -> bool: pass


class LocalStorage(BaseStorage):
    """本地存储实现"""
    def __init__(self, base_dir: str = None):
        from pathlib import Path
        self.base_dir = Path(base_dir or settings.UPLOAD_ROOT)

    async def upload(self, key: str, data: bytes, content_type: str) -> str:
        path = self.base_dir / key
        path.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(path, 'wb') as f:
            await f.write(data)
        return f"/uploads/{key}"

    async def upload_multiple(self, files: Dict[str, bytes], prefix: str) -> Dict[str, str]:
        results = {}
        for name, data in files.items():
            key = f"{prefix}/{name}"
            results[name] = await self.upload(key, data, "image/webp")
        return results

    async def delete(self, key: str) -> bool:
        path = self.base_dir / key
        if path.exists():
            path.unlink()
            return True
        return False


class OSSStorage(BaseStorage):
    """OSS 存储实现（预留，未来启用）"""
    def __init__(self):
        import oss2
        self.auth = oss2.Auth(settings.OSS_ACCESS_KEY, settings.OSS_SECRET_KEY)
        self.bucket = oss2.Bucket(self.auth, settings.OSS_ENDPOINT, settings.OSS_BUCKET)
        self.cdn_domain = settings.CDN_DOMAIN

    async def upload(self, key: str, data: bytes, content_type: str) -> str:
        def _upload():
            self.bucket.put_object(key, data, content_type=content_type)
            return f"https://{self.cdn_domain}/{key}"
        return await asyncio.get_event_loop().run_in_executor(None, _upload)

    async def upload_multiple(self, files: Dict[str, bytes], prefix: str) -> Dict[str, str]:
        results = {}
        for name, data in files.items():
            key = f"{prefix}/{name}"
            results[name] = await self.upload(key, data, "image/webp")
        return results

    async def delete(self, key: str) -> bool:
        def _delete():
            return self.bucket.delete_object(key).status == 204
        return await asyncio.get_event_loop().run_in_executor(None, _delete)


class StorageFactory:
    """存储工厂：根据配置切换实现"""
    _providers: Dict[str, BaseStorage] = {}

    @classmethod
    def get(cls) -> BaseStorage:
        provider = getattr(settings, 'STORAGE_PROVIDER', 'local')
        if provider == 'oss':
            if 'oss' not in cls._providers:
                cls._providers['oss'] = OSSStorage()
            return cls._providers['oss']
        if 'local' not in cls._providers:
            cls._providers['local'] = LocalStorage()
        return cls._providers['local']
```

### 11.3 配置项

```env
# .env
STORAGE_PROVIDER=local
UPLOAD_ROOT=/var/www/blog/uploads

# OSS 配置（预留，未来启用时取消注释）
# STORAGE_PROVIDER=oss
# OSS_ACCESS_KEY=your-access-key
# OSS_SECRET_KEY=your-secret-key
# OSS_ENDPOINT=oss-cn-hangzhou.aliyuncs.com
# OSS_BUCKET=your-bucket-name
# CDN_DOMAIN=cdn.yourdomain.com
```

### 11.4 Nginx 静态文件服务

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    # 静态资源
    location /uploads/ {
        alias /var/www/blog/uploads/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # WebP 图片 gzip
    location ~* \.(webp)$ {
        gzip on;
        gzip_types image/webp;
        expires 1y;
    }
}
```

### 11.5 数据库表结构

```sql
-- 头像表
avatars (
  id UUID PRIMARY KEY,
  user_id UUID UNIQUE REFERENCES users(id),
  path_sm VARCHAR(500),          -- sm.webp
  path_md VARCHAR(500),          -- md.webp
  path_lg VARCHAR(500),          -- lg.webp
  url VARCHAR(500),             -- 访问 URL
  file_size INTEGER,
  width INTEGER,
  height INTEGER,
  format VARCHAR(10),
  created_at TIMESTAMP
)

-- 博客图片表
blog_images (
  id UUID PRIMARY KEY,
  blog_id UUID REFERENCES blogs(id),
  uploader_id UUID REFERENCES users(id),
  path_original VARCHAR(500),
  path_compressed VARCHAR(500),
  path_thumbnail VARCHAR(500),
  path_mobile VARCHAR(500),
  url VARCHAR(500),
  url_thumbnail VARCHAR(500),
  file_size INTEGER,
  width INTEGER,
  height INTEGER,
  format VARCHAR(10),
  is_cover BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP
)
```

### 11.6 上传 API 实现

```python
# upload/views.py
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException

router = APIRouter(prefix="/upload", tags=["上传"])

ALLOWED_TYPES = ["image/jpeg", "image/png", "image/webp", "image/gif"]
MAX_AVATAR_SIZE = 5 * 1024 * 1024    # 5MB
MAX_BLOG_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB

storage = StorageFactory.get()

@router.post("/avatar")
async def upload_avatar(file: UploadFile = File(...), user = Depends(get_current_user)):
    if file.size > MAX_AVATAR_SIZE:
        raise HTTPException(400, "文件超过 5MB")
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(400, "仅支持 jpg/png/webp/gif")

    image_data = await file.read()
    processor = ImageProcessor()
    variants = processor.process_avatar(image_data)

    prefix = f"avatars/{user.id}"
    urls = await storage.upload_multiple(variants, prefix)

    avatar = await Avatar.update_or_create(
        user_id=user.id,
        defaults={
            "path_sm": f"{prefix}/sm.webp",
            "path_md": f"{prefix}/md.webp",
            "path_lg": f"{prefix}/lg.webp",
            "url": urls.get("lg"),
            "format": "webp",
        }
    )
    return {"url": avatar.url, "sm": urls.get("sm"), "md": urls.get("md"), "lg": urls.get("lg")}


@router.post("/blog-image")
async def upload_blog_image(
    file: UploadFile = File(...),
    blog_id: UUID,
    user = Depends(get_current_user)
):
    if file.size > MAX_BLOG_IMAGE_SIZE:
        raise HTTPException(400, "文件超过 10MB")
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(400, "不支持的图片格式")

    # 频率限制（Redis）
    rate_key = f"upload:rate:{user.id}"
    count = await redis.incr(rate_key)
    if count == 1:
        await redis.expire(rate_key, 60)
    if count > 20:
        raise HTTPException(429, "上传过于频繁")

    image_data = await file.read()
    processor = ImageProcessor()
    variants = processor.process_blog_image(image_data)

    prefix = f"blogs/{blog_id}"
    urls = await storage.upload_multiple(variants, prefix)

    blog_image = await BlogImage.create(
        blog_id=blog_id,
        uploader_id=user.id,
        url=urls.get("compressed"),
        url_thumbnail=urls.get("thumbnail"),
    )
    return {"url": blog_image.url, "thumbnail": blog_image.url_thumbnail}
```

### 11.7 图片处理服务

```python
# core/image.py
from PIL import Image
from io import BytesIO
from typing import Dict

class ImageProcessor:
    """图片处理工具"""
    AVATAR_SIZES = [48, 128, 256]
    BLOG_SIZES = {"original": 4000, "compressed": 2000, "thumbnail": 400, "mobile": 1080}
    QUALITY = 85

    def process_avatar(self, image_data: bytes) -> Dict[str, bytes]:
        img = self._normalize(image_data)
        results = {}
        size_map = {48: "sm", 128: "md", 256: "lg"}
        for size in self.AVATAR_SIZES:
            resized = img.copy()
            resized.thumbnail((size, size), Image.LANCZOS)
            results[size_map[size]] = self._to_webp(resized)
        return results

    def process_blog_image(self, image_data: bytes) -> Dict[str, bytes]:
        img = self._normalize(image_data)
        w, h = img.size
        results = {}
        for variant, max_size in self.BLOG_SIZES.items():
            if variant == "original":
                if max(w, h) > max_size:
                    ratio = max_size / max(w, h)
                    img_copy = img.resize((int(w*ratio), int(h*ratio)), Image.LANCZOS)
                else:
                    img_copy = img
            else:
                img_copy = img.copy()
                img_copy.thumbnail((max_size, max_size), Image.LANCZOS)
            results[variant] = self._to_webp(img_copy, quality=self.QUALITY)
        return results

    def _normalize(self, image_data: bytes) -> Image.Image:
        img = Image.open(BytesIO(image_data))
        if img.mode == "RGBA":
            background = Image.new("RGB", img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[3])
            img = background
        return img

    def _to_webp(self, img: Image.Image, quality: int = 85) -> bytes:
        output = BytesIO()
        img.save(output, format="WEBP", quality=quality)
        return output.getvalue()
```

### 11.8 前端图片组件

```vue
<!-- OptimizedImage.vue -->
<template>
  <div class="image-wrapper" :class="{ loaded: isLoaded, error: hasError }">
    <div v-if="!isLoaded && !hasError" class="skeleton" />
    <div v-if="hasError" class="error-placeholder">图片加载失败</div>
    <img
      v-show="isLoaded"
      :src="currentSrc"
      :srcset="srcset"
      :sizes="sizes"
      :alt="alt"
      @load="isLoaded = true"
      @error="hasError = true"
      :loading="lazy ? 'lazy' : 'eager'"
      decoding="async"
    />
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  src: String,
  srcSm: String, srcMd: String, srcLg: String,
  alt: String, sizes: String, lazy: Boolean
})

const isLoaded = ref(false), hasError = ref(false)

const currentSrc = computed(() => {
  const isMobile = window.innerWidth < 768
  return isMobile ? (props.srcMd || props.src) : (props.srcLg || props.src)
})

const srcset = computed(() => {
  const parts = []
  if (props.srcSm) parts.push(`${props.srcSm} 400w`)
  if (props.srcMd) parts.push(`${props.srcMd} 800w`)
  if (props.srcLg) parts.push(`${props.srcLg} 1200w`)
  return parts.join(', ')
})
</script>

<style scoped>
.image-wrapper { position: relative; overflow: hidden; background: #f5f5f5; }
.skeleton {
  position: absolute; inset: 0;
  background: linear-gradient(90deg, #eee 25%, #ddd 50%, #eee 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}
@keyframes shimmer { 0% { background-position: 200% 0; } 100% { background-position: -200% 0; } }
.image-wrapper img { width: 100%; height: auto; transition: opacity 0.3s; }
.image-wrapper:not(.loaded) img { opacity: 0; }
</style>
```

```vue
<!-- Avatar.vue -->
<template>
  <div class="avatar" :class="`avatar--${size}`">
    <img v-if="src && !hasError" :src="src" :alt="alt" @error="hasError = true" @load="isLoaded = true"
      :class="{ 'avatar--loaded': isLoaded }" />
    <div v-else class="avatar__default">
      <svg viewBox="0 0 24 24" fill="currentColor">
        <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
      </svg>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
const props = defineProps({
  src: String, srcSm: String, srcMd: String, srcLg: String,
  size: { type: String, default: 'md' }, alt: { type: String, default: '头像' }
})
const isLoaded = ref(false), hasError = ref(false)
const src = computed(() => {
  const map = { sm: 'srcSm', md: 'srcMd', lg: 'srcLg' }
  return props[map[props.size]] || props.src
})
</script>

<style scoped>
.avatar { border-radius: 50%; overflow: hidden; background: #e0e0e0; }
.avatar--sm { width: 32px; height: 32px; }
.avatar--md { width: 48px; height: 48px; }
.avatar--lg { width: 96px; height: 96px; }
.avatar img { width: 100%; height: 100%; object-fit: cover; opacity: 0; transition: opacity 0.3s; }
.avatar img.avatar--loaded { opacity: 1; }
.avatar__default { width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; color: #9e9e9e; }
.avatar__default svg { width: 60%; height: 60%; }
</style>
```

### 11.9 缓存策略说明

| 概念 | 说明 |
|------|------|
| **CDN 缓存 1 年** | `Cache-Control: public, max-age=31536000`，图片缓存 1 年，极速加载 |
| **幂等 URL** | 同一 URL 返回相同内容。更新资源（如换头像）时通过改变 URL（加 `?v=时间戳`）让缓存失效 |

### 11.10 费用说明

| 阶段 | 存储方式 | 费用 |
|------|----------|------|
| **当前** | 本地存储 | 无额外费用（用服务器磁盘） |
| **未来** | OSS + CDN | OSS 存储费极低（0.12元/GB/月），CDN 流量按量收费，缓存命中越高费用越低 |

## 11. 开发周期估算

| 阶段 | 建议周期 | 说明 |
|------|----------|------|
| 项目初始化 | 3-5 天 | 脚手架、CI/CD、数据库、基础架构 |
| 用户+认证 | 5-7 天 | 注册/登录/JWT/管理后台用户管理 |
| 博客模块 | 7-10 天 | CRUD + 审核 + Markdown 编辑器 |
| 评论模块 | 5-7 天 | 评论 + 嵌套 + 敏感词审核 |
| 收藏/点赞/关注 | 5-7 天 | 互动功能 |
| 动态模块 | 5-7 天 | 动态流 |
| 敏感词审核 | 3-5 天 | DFA 算法 + 审核流程 |
| Celery 任务 | 3-5 天 | 邮件/计数/定时任务 |
| 百日筑基 | 5-7 天 | 打卡 + 计时器 + 成就系统 |
| 管理后台 | 7-10 天 | 数据统计 + 管理功能 |
| 测试+优化 | 持续 | 自动化测试、性能优化 |

**总计约 50-70 人天**（视团队规模和经验而定）
