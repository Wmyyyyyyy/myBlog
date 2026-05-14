# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Full-stack blog system**: Vue 3 + FastAPI + PostgreSQL + Redis + Celery + Vite + Pinia + Element Plus + ECharts

Key features: user dynamics, blog publishing/management, comments, favorites/likes/follows, sensitive word moderation, admin panel, and "百日筑基" (100-day habit tracking).

### Prerequisites
- Python 3.11+
- Node.js 20+
- PostgreSQL 14+
- Redis 7+

### Running the Application

**Backend:**
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

**Frontend:**
```bash
cd web-client
npm install
npm run dev
```

**Celery:**
```bash
celery -A celery_worker worker --loglevel=info
```

## Architecture

### Backend Structure (FastAPI)
```
backend/
├── apps/
│   ├── users/         # User system
│   ├── blogs/         # Blog module
│   ├── comments/      # Comment module
│   ├── interactions/  # Favorites/likes/follows
│   ├── dynamics/      # User activity feed
│   ├── moderation/    # DFA sensitive word detection
│   ├── foundation/    # 百日筑基 habit tracking
│   └── upload/        # Image upload
├── core/
│   ├── config.py      # Settings management
│   ├── database.py    # Async PostgreSQL (SQLAlchemy)
│   ├── redis.py       # Redis connection
│   ├── security.py    # JWT/password hashing
│   └── dependencies.py # FastAPI dependency injection
├── tasks/             # Celery async tasks
└── main.py            # FastAPI entry point
```

### Frontend Structure (Vue 3)
```
web-client/src/
├── api/               # API call wrappers
├── components/        # Reusable components
├── composables/       # Composition API functions
├── stores/            # Pinia state stores
├── views/             # Page components
└── router/
```

### Key Technical Decisions

**DFA Algorithm for Sensitive Words**: Deterministic Finite Automaton for O(n) text scanning. Supports simplified/traditional Chinese conversion, full-width/half-width normalization. Three action levels: block, replace, warn.

**Image Storage**: Local storage by default with OSS interface预留. Generates multiple sizes: avatars (48/128/256px), blog images (original/compressed/thumbnail/mobile).

**API Response Format**:
```json
{"code": 0, "message": "success", "data": {...}}
```
Error: `{"code": 40001, "message": "Validation error", "errors": {...}}`

## Development Guidelines

### Core Principles

**必须严格遵循以下四个核心原则。**

#### 1. 编码前思考
**不要假设 — 不确定时，询问而不是猜测。**
- 明确陈述假设，不确定时就提问
- 存在多种解释时，列出利弊而非默默选择
- 有更简单的方案时，指出并推动
- 困惑时停下来，指出不清楚的地方

#### 2. 简洁优先
**用最少的代码解决问题，不添加 speculative 代码。**
- 不添加要求之外的功能
- 不为一次性代码创建抽象
- 不添加未请求的"灵活性"或"可配置性"
- 不处理不可能发生的错误场景
- 如果 200 行可以写成 50 行，重写它

#### 3. 精准修改
**只改该改的，不碰无关代码。**
- 不"改进"相邻的代码、注释或格式
- 不重构没坏的东西
- 匹配现有风格，即使你更倾向于不同的写法
- 发现无关的死代码时提及，不删除
- 更改创建的孤儿代码（未使用的导入/变量/函数）要清理

#### 4. 目标驱动执行
**定义可验证的成功标准，逐步验证。**
将任务转化为可验证的目标：
- "添加验证" → "为无效输入写测试，然后让它们通过"
- "修复 bug" → "写一个复现 bug 的测试，然后让它通过"
- "重构 X" → "确保重构前后测试都通过"

多步骤任务要说明简短计划并逐步验证。

**检验标准：每行修改都应该能直接追溯到用户的请求。**

### API 规范

**路径命名：**
- 使用复数名词：`/api/users`、`/api/blogs`
- 嵌套资源：`/api/blogs/{id}/comments`

**版本控制：**
- URL 路径版本：`/api/v1/users`
- 保持向后兼容

**错误码结构：** `<模块><序号>`
- 40001 = 通用模块验证错误
- 40010 = 用户模块验证错误

## Testing & Quality

**Backend:** pytest + pytest-asyncio + httpx
```bash
pytest --cov=apps --cov-report=html
pytest tests/apps/blogs/  # single module
pytest -n auto            # parallel
```

**Frontend:** vitest + @vue/test-utils + Playwright E2E
```bash
npm run test
npm run test:coverage
npm run test:e2e
```

**CI/CD:** GitHub Actions with Docker Compose

## Execution Rules

### TDD 强制
- 所有新功能必须先写测试
- 测试失败后才能写实现代码
- 重构前后必须保证测试通过

### Code Review 强制
- 提交前必须进行 self-review
- 检查：是否遵循 Core Principles、是否有死代码、是否匹配现有风格

### Simplify 强制
- 每次提交代码前自动调用 simplify skill 进行代码审查
- 修改涉及多个文件时，必须使用 `/simplify` 检查代码复用性、质量和效率问题

### Debugging 规则
- 遇到 bug 必须先调用 debugging skill
- 修复后 grep 相似模式，防止遗漏

### Cross-Testing 规则
- 后端修改后立即测试前端对应组件
- 前端修改后立即测试后端对应组件

## Subagent Usage

每次对话开始时，自动评估是否需要启动子代理（Agent 工具）来并行执行独立任务。
