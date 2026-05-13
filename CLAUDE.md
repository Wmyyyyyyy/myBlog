# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Full-stack blog system rewrite**: Vue 3 + FastAPI + PostgreSQL + Redis + Celery + Vite + Pinia + Element Plus + ECharts

Key features: user dynamics, blog publishing/management, comments, favorites/likes/follows, sensitive word moderation, admin panel, and "百日筑基" (100-day habit tracking).

## Development Environment

### Prerequisites
- Python 3.11+ (FastAPI)
- Node.js 20+ (Vite/Vue)
- PostgreSQL 14+
- Redis 7+

### Running the Application

**Backend:**
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
# API docs at http://localhost:8000/docs
```

**Frontend:**
```bash
cd web-client
npm install
npm run dev
```

**Celery Worker:**
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

### Database
- PostgreSQL with async SQLAlchemy (asyncpg)
- Redis for caching + Celery broker
- Alembic for migrations (planned)

### Key Technical Decisions

**DFA Algorithm for Sensitive Words**: Uses Deterministic Finite Automaton for O(n) text scanning. Supports simplified/traditional Chinese conversion, full-width/half-width normalization. Three action levels: block (reject), replace (auto-replace with ****), warn (allow with warning).

**Image Storage**: Local storage by default with OSS interface预留. Generates multiple sizes: avatars (48/128/256px), blog images (original/compressed/thumbnail/mobile).

**API Response Format**:
```json
{"code": 0, "message": "success", "data": {...}}
```
Error: `{"code": 40001, "message": "Validation error", "errors": {...}}`

## Testing

**Backend:** pytest + pytest-asyncio + httpx (async)
```bash
pytest --cov=apps --cov-report=html
pytest tests/apps/blogs/  # single module
pytest -n auto            # parallel
```

**Frontend:** vitest + @vue/test-utils + Playwright E2E
```bash
npm run test            # unit tests
npm run test:coverage   # with coverage
npm run test:e2e        # E2E tests
```

**CI/CD:** GitHub Actions with Docker Compose test environment

## Milestones

| Phase | Focus | Duration |
|-------|-------|----------|
| M1 | Project scaffolding, CI/CD, DB setup | 1 week |
| M2 | Users + authentication + JWT | 1.5 weeks |
| M3 | Blogs + comments + moderation | 2 weeks |
| M4 | Interactions + dynamics feed | 1.5 weeks |
| M5 | Admin panel + statistics | 2 weeks |
| M6 | Testing + deployment | ongoing |

## Common Tasks

**Add a new sensitive word:**
1. POST to `/api/admin/sensitive-words` with `{word, level, action}`
2. Celery task reloads DFA tree from DB

**Create a new blog:**
1. User submits blog → sensitive word check via DFA
2. If blocked → return 400; if replace → auto-replace words
3. Save to DB, create activity in dynamics feed

**百日筑基 check-in:**
1. POST `/api/foundation/checkin` → increment streak
2. Check achievements (7/30/100 day milestones)
3. Celery Beat resets daily data at 4am
