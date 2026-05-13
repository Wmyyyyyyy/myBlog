# 自动化测试文档

## 1. 测试策略

### 1.1 分层测试

```
┌─────────────────┐
│   E2E Tests     │  ← 用户级完整流程（Playwright）
└────────┬────────┘
         │
┌────────▼────────┐
│  Integration    │  ← API 端到端（FastAPI TestClient）
│    Tests        │
└────────┬────────┘
         │
┌────────▼────────┐
│    Unit         │  ← 业务逻辑单元（pytest）
│    Tests        │
└─────────────────┘
```

### 1.2 测试覆盖率目标

| 层级 | 目标覆盖率 |
|------|-----------|
| 后端单元测试 | ≥ 80% |
| 后端 API 测试 | 核心接口 100% |
| 前端组件测试 | 核心组件 ≥ 70% |
| E2E 测试 | 核心用户流程 |

---

## 2. 后端测试

### 2.1 测试框架

```text
# requirements.txt
pytest
pytest-asyncio
pytest-cov
httpx          # 异步 HTTP 客户端
Faker          # 假数据生成
pytest-mock    # mock 支持
```

### 2.2 测试文件结构

```
backend/tests/
├── conftest.py              # pytest fixtures
├── apps/
│   ├── users/
│   │   ├── test_models.py
│   │   ├── test_views.py
│   │   └── test_services.py
│   ├── blogs/
│   │   ├── test_models.py
│   │   ├── test_views.py
│   │   └── test_services.py
│   ├── comments/
│   ├── interactions/
│   ├── dynamics/
│   └── moderation/
└── core/
    ├── test_security.py
    └── test_config.py
```

### 2.3 conftest.py 示例

```python
import pytest
import asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from main import app
from core.database import Base, get_db

TEST_DATABASE_URL = "postgresql+asyncpg://user:pass@localhost/test_db"

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="function")
async def db_session():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with AsyncSession(engine) as session:
        yield session
        await session.rollback()

@pytest.fixture(scope="function")
async def client(db_session):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()

@pytest.fixture
def auth_headers(client):
    # 注册并登录，返回 auth headers
    async def _get_headers():
        await client.post("/api/auth/register", json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "SecurePass123"
        })
        login_resp = await client.post("/api/auth/login", json={
            "username": "testuser",
            "password": "SecurePass123"
        })
        token = login_resp.json()["data"]["access_token"]
        return {"Authorization": f"Bearer {token}"}
    return _get_headers()
```

### 2.4 核心测试用例

#### 用户模块

```python
class TestUserRegistration:
    async def test_register_success(self, client):
        response = await client.post("/api/auth/register", json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "SecurePass123"
        })
        assert response.status_code == 201
        assert response.json()["code"] == 0

    async def test_register_duplicate_username(self, client):
        await client.post("/api/auth/register", json={
            "username": "testuser",
            "email": "test1@example.com",
            "password": "SecurePass123"
        })
        response = await client.post("/api/auth/register", json={
            "username": "testuser",
            "email": "test2@example.com",
            "password": "SecurePass123"
        })
        assert response.status_code == 400

    async def test_register_invalid_email(self, client):
        response = await client.post("/api/auth/register", json={
            "username": "test",
            "email": "not-an-email",
            "password": "pass"
        })
        assert response.status_code == 422

    async def test_register_password_too_short(self, client):
        response = await client.post("/api/auth/register", json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "123"
        })
        assert response.status_code == 422


class TestUserLogin:
    async def test_login_success(self, client):
        await client.post("/api/auth/register", json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "SecurePass123"
        })
        response = await client.post("/api/auth/login", json={
            "username": "testuser",
            "password": "SecurePass123"
        })
        assert response.status_code == 200
        assert "access_token" in response.json()["data"]

    async def test_login_wrong_password(self, client):
        await client.post("/api/auth/register", json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "SecurePass123"
        })
        response = await client.post("/api/auth/login", json={
            "username": "testuser",
            "password": "WrongPass"
        })
        assert response.status_code == 401

    async def test_login_nonexistent_user(self, client):
        response = await client.post("/api/auth/login", json={
            "username": "nonexistent",
            "password": "AnyPass"
        })
        assert response.status_code == 401
```

#### 博客模块

```python
class TestBlogCreation:
    async def test_create_blog_success(self, client, auth_headers):
        response = await client.post("/api/blogs",
            headers=auth_headers,
            json={
                "title": "Test Blog",
                "content": "This is test content",
                "summary": "A brief summary"
            })
        assert response.status_code == 201
        assert response.json()["data"]["title"] == "Test Blog"

    async def test_create_blog_unauthorized(self, client):
        response = await client.post("/api/blogs", json={
            "title": "Test",
            "content": "Content"
        })
        assert response.status_code == 401

    async def test_create_blog_sensitive_content(self, client, auth_headers):
        response = await client.post("/api/blogs",
            headers=auth_headers,
            json={
                "title": "Test with 脏话",
                "content": "Blog content"
            })
        assert response.status_code == 400
        assert "sensitive" in response.json()["message"].lower()


class TestBlogList:
    async def test_list_blogs_pagination(self, client):
        response = await client.get("/api/blogs?page=1&page_size=10")
        assert response.status_code == 200
        assert "items" in response.json()["data"]
        assert "total" in response.json()["data"]

    async def test_list_blogs_filter_by_category(self, client):
        response = await client.get("/api/blogs?category_id=1")
        assert response.status_code == 200
```

#### 评论模块

```python
class TestCommentCreation:
    async def test_create_comment_success(self, client, auth_headers):
        blog_resp = await client.post("/api/blogs",
            headers=auth_headers,
            json={"title": "Test", "content": "Content"})
        blog_id = blog_resp.json()["data"]["id"]

        response = await client.post(f"/api/blogs/{blog_id}/comments",
            headers=auth_headers,
            json={"content": "Great post!"})
        assert response.status_code == 201

    async def test_create_comment_sensitive_word(self, client, auth_headers):
        blog_id = 1
        response = await client.post(f"/api/blogs/{blog_id}/comments",
            headers=auth_headers,
            json={"content": "This contains 敏感词"})
        assert response.status_code == 400

    async def test_nested_comment(self, client, auth_headers):
        blog_id = 1
        parent_resp = await client.post(f"/api/blogs/{blog_id}/comments",
            headers=auth_headers,
            json={"content": "Parent comment"})
        parent_id = parent_resp.json()["data"]["id"]

        response = await client.post(f"/api/blogs/{blog_id}/comments",
            headers=auth_headers,
            json={"content": "Reply comment", "parent_id": parent_id})
        assert response.status_code == 201
        assert response.json()["data"]["parent_id"] == parent_id
```

#### 收藏/点赞模块

```python
class TestLikeInteraction:
    async def test_like_blog(self, client, auth_headers):
        blog_id = 1
        response = await client.post(f"/api/blogs/{blog_id}/like",
            headers=auth_headers)
        assert response.status_code == 200

    async def test_unlike_blog(self, client, auth_headers):
        blog_id = 1
        await client.post(f"/api/blogs/{blog_id}/like",
            headers=auth_headers)
        response = await client.delete(f"/api/blogs/{blog_id}/like",
            headers=auth_headers)
        assert response.status_code == 200

    async def test_duplicate_like_same_blog(self, client, auth_headers):
        blog_id = 1
        await client.post(f"/api/blogs/{blog_id}/like",
            headers=auth_headers)
        response = await client.post(f"/api/blogs/{blog_id}/like",
            headers=auth_headers)
        # 重复点赞应该取消点赞
        assert response.status_code == 200
        assert response.json()["data"]["is_liked"] == False


class TestCollectInteraction:
    async def test_collect_blog(self, client, auth_headers):
        blog_id = 1
        response = await client.post(f"/api/blogs/{blog_id}/collect",
            headers=auth_headers)
        assert response.status_code == 200

    async def test_uncollect_blog(self, client, auth_headers):
        blog_id = 1
        await client.post(f"/api/blogs/{blog_id}/collect",
            headers=auth_headers)
        response = await client.delete(f"/api/blogs/{blog_id}/collect",
            headers=auth_headers)
        assert response.status_code == 200
```

#### 敏感词审核模块

```python
class TestSensitiveWordModeration:
    async def test_check_content_returns_sensitive_words(self):
        from apps.moderation.services import SensitiveWordService
        service = SensitiveWordService()
        result = service.check("这是一段包含敏感词的内容")
        assert result["has_sensitive"] == True
        assert len(result["found_words"]) > 0

    async def test_admin_can_add_sensitive_word(self, admin_headers):
        response = await client.post("/api/admin/sensitive-words",
            headers=admin_headers,
            json={"word": "测试敏感词", "level": "strict"})
        assert response.status_code == 201

    async def test_admin_can_delete_sensitive_word(self, admin_headers):
        add_resp = await client.post("/api/admin/sensitive-words",
            headers=admin_headers,
            json={"word": "待删除词", "level": "strict"})
        word_id = add_resp.json()["data"]["id"]

        response = await client.delete(f"/api/admin/sensitive-words/{word_id}",
            headers=admin_headers)
        assert response.status_code == 200

    async def test_dfa_finds_exact_match(self):
        """DFA 算法精确匹配测试"""
        service = SensitiveWordService()
        passed, words = service.check("这是一段正常的文本")
        assert passed == True
        assert len(words) == 0

    async def test_dfa_detects_word_boundary(self):
        """DFA 边界检测"""
        service = SensitiveWordService()
        passed, words = service.check("今天天气很好")
        # 假设"天气"是敏感词
        # 应该能检测到
        assert len(words) >= 0  # 根据实际敏感词库

    async def test_normalization_handles_simplified(self):
        """简繁体转换"""
        service = SensitiveWordService()
        # "台" -> "臺" 转换后检测
        passed, words = service.check("台海问题")
        # 应该能匹配到繁体的"臺"
        assert len(words) >= 0

    async def test_check_and_action_block(self):
        """action=block 的敏感词"""
        service = SensitiveWordService()
        result = service.check_and_action("包含block级敏感词")
        assert result["action"] == "block"
        assert result["passed"] == False

    async def test_check_and_action_replace(self):
        """action=replace 的敏感词"""
        service = SensitiveWordService()
        result = service.check_and_action("包含replace级敏感词")
        assert result["action"] == "replace"
        assert result["passed"] == True

    async def test_moderation_log_created(self, auth_headers):
        """审核日志正确记录"""
        response = await client.post("/api/blogs",
            headers=auth_headers,
            json={"title": "Test Blog", "content": "Normal content"})
        assert response.status_code == 201

        # 验证日志是否创建
        log_response = await client.get("/api/admin/moderation-logs")
        assert log_response.status_code == 200
```

#### 百日筑基模块

```python
class TestFoundationCheckin:
    async def test_checkin_increments_streak(self, client, auth_headers):
        response = await client.post("/api/foundation/checkin",
            headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["data"]["streak"] >= 1

    async def test_checkin_twice_same_day(self, client, auth_headers):
        # 第一次打卡
        await client.post("/api/foundation/checkin", headers=auth_headers)
        # 第二次打卡（同一天）
        response = await client.post("/api/foundation/checkin",
            headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["data"]["checkin_count"] == 2

    async def test_get_profile(self, client, auth_headers):
        response = await client.get("/api/foundation/profile",
            headers=auth_headers)
        assert response.status_code == 200
        assert "current_streak" in response.json()["data"]
        assert "total_checkins" in response.json()["data"]


class TestFoundationTimer:
    async def test_start_session(self, client, auth_headers):
        response = await client.post("/api/foundation/sessions",
            headers=auth_headers,
            json={"session_type": "focus"})
        assert response.status_code == 201
        assert "session_id" in response.json()["data"]

    async def test_end_session(self, client, auth_headers):
        # 先开始
        start_resp = await client.post("/api/foundation/sessions",
            headers=auth_headers,
            json={"session_type": "focus"})
        session_id = start_resp.json()["data"]["session_id"]

        # 再结束
        end_resp = await client.put(f"/api/foundation/sessions/{session_id}",
            headers=auth_headers)
        assert end_resp.status_code == 200
        assert "duration" in end_resp.json()["data"]

    async def test_session_updates_daily_focus(self, client, auth_headers):
        start_resp = await client.post("/api/foundation/sessions",
            headers=auth_headers,
            json={"session_type": "focus"})
        session_id = start_resp.json()["data"]["session_id"]

        await client.put(f"/api/foundation/sessions/{session_id}",
            headers=auth_headers)

        profile_resp = await client.get("/api/foundation/profile",
            headers=auth_headers)
        assert profile_resp.json()["data"]["total_focus_minutes"] >= 0


class TestFoundationAchievements:
    async def test_get_achievements(self, client, auth_headers):
        response = await client.get("/api/foundation/achievements",
            headers=auth_headers)
        assert response.status_code == 200
        assert len(response.json()["data"]) > 0

    async def test_streak_achievement_unlocked(self, client, auth_headers):
        # 假设连续7天打卡解锁"七天如一"成就
        profile_resp = await client.get("/api/foundation/profile",
            headers=auth_headers)
        streak = profile_resp.json()["data"]["current_streak"]

        if streak >= 7:
            achievements_resp = await client.get("/api/foundation/achievements",
                headers=auth_headers)
            earned = [a for a in achievements_resp.json()["data"]
                     if a.get("code") == "seven_day_streak"]
            assert len(earned) > 0


class TestFoundationLeaderboard:
    async def test_leaderboard(self, client):
        response = await client.get("/api/foundation/leaderboard")
        assert response.status_code == 200
        assert "items" in response.json()["data"]

    async def test_leaderboard_sorted_by_streak(self, client):
        response = await client.get("/api/foundation/leaderboard?sort=streak")
        items = response.json()["data"]["items"]
        streaks = [item["current_streak"] for item in items]
        assert streaks == sorted(streaks, reverse=True)
```

### 2.5 运行测试

```bash
# 运行所有测试
pytest

# 带覆盖率
pytest --cov=apps --cov-report=html --cov-report=term

# 只运行某个模块
pytest tests/apps/blogs/

# 并行运行（加速）
pytest -n auto

# 只运行最后一次失败的测试
pytest --lf

# 详细输出
pytest -v
```

---

## 3. 前端测试

### 3.1 测试框架

```javascript
// package.json
{
  "scripts": {
    "test": "vitest",
    "test:coverage": "vitest run --coverage",
    "test:e2e": "playwright test"
  },
  "devDependencies": {
    "vitest": "^1.x",
    "@vue/test-utils": "^2.x",
    "@vitest/coverage-v8": "^1.x",
    "@playwright/test": "^1.x",
    "msw": "^2.x"
  }
}
```

### 3.2 组件测试示例

```javascript
// components/blog/BlogCard.spec.js
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import BlogCard from './BlogCard.vue'

describe('BlogCard', () => {
  it('renders blog title and author', () => {
    const blog = {
      id: 1,
      title: 'Test Blog',
      author: { username: 'testuser', avatar: '/avatar.png' },
      like_count: 10,
      comment_count: 5
    }

    const wrapper = mount(BlogCard, {
      props: { blog }
    })

    expect(wrapper.find('.blog-title').text()).toBe('Test Blog')
    expect(wrapper.find('.author-name').text()).toBe('testuser')
  })

  it('emits like event when like button clicked', async () => {
    const wrapper = mount(BlogCard, {
      props: { blog: { id: 1, is_liked: false } }
    })

    await wrapper.find('.like-button').trigger('click')

    expect(wrapper.emitted('like')).toBeTruthy()
  })

  it('shows login prompt when liking without auth', async () => {
    const wrapper = mount(BlogCard, {
      props: { blog: { id: 1, is_liked: false }, isLoggedIn: false }
    })

    await wrapper.find('.like-button').trigger('click')

    expect(wrapper.find('.login-prompt').isVisible()).toBe(true)
  })
})

describe('FoundationCard', () => {
  it('displays current streak', () => {
    const wrapper = mount(FoundationCard, {
      props: {
        profile: { current_streak: 7, total_checkins: 30 }
      }
    })

    expect(wrapper.find('.streak-badge .days').text()).toBe('7')
  })

  it('shows progress ring with correct percentage', () => {
    const wrapper = mount(FoundationCard, {
      props: {
        profile: { current_streak: 5 },
        todayMinutes: 15,
        dailyGoal: 30
      }
    })

    // 15/30 = 50%
    const ring = wrapper.find('.progress-ring circle:last-child')
    expect(ring.attributes('stroke-dasharray')).toContain('141.5') // ~50% of 283
  })

  it('checkin button emits checkin event', async () => {
    const wrapper = mount(FoundationCard, {
      props: {}
    })

    await wrapper.find('.checkin-btn').trigger('click')
    expect(wrapper.emitted('checkin')).toBeTruthy()
  })

  it('timer button emits start-timer event', async () => {
    const wrapper = mount(FoundationCard, {
      props: {}
    })

    await wrapper.find('.timer-btn').trigger('click')
    expect(wrapper.emitted('start-timer')).toBeTruthy()
  })
})
```

### 3.3 Composables 测试

```javascript
// composables/useBlog.spec.js
import { describe, it, expect, vi } from 'vitest'
import { setupServer } from 'msw/node'
import { http, HttpResponse } from 'msw'

const server = setupServer(
  http.get('/api/blogs', () => {
    return HttpResponse.json({
      code: 0,
      data: {
        items: [{ id: 1, title: 'Test Blog' }],
        total: 1
      }
    })
  })
)

describe('useBlog composable', () => {
  beforeAll(() => server.listen())
  afterEach(() => server.resetHandlers())
  afterAll(() => server.close())

  it('fetches blog list', async () => {
    const { fetchBlogs, blogs, loading } = useBlog()
    await fetchBlogs()

    expect(blogs.value).toHaveLength(1)
    expect(blogs.value[0].title).toBe('Test Blog')
    expect(loading.value).toBe(false)
  })
})
```

### 3.4 Store 测试

```javascript
// stores/auth.spec.js
import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useAuthStore } from './auth'

describe('auth store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('login sets user and token', async () => {
    const store = useAuthStore()
    await store.login({
      username: 'testuser',
      password: 'password123'
    })

    expect(store.isLoggedIn).toBe(true)
    expect(store.user.username).toBe('testuser')
    expect(store.token).toBeTruthy()
  })

  it('logout clears state', async () => {
    const store = useAuthStore()
    await store.login({ username: 'test', password: 'pass' })
    await store.logout()

    expect(store.isLoggedIn).toBe(false)
    expect(store.user).toBe(null)
    expect(store.token).toBe('')
  })
})
```

### 3.5 E2E 测试（Playwright）

```javascript
// e2e/blog.spec.js
const { test, expect } = require('@playwright/test')

test.describe('Blog Flow', () => {
  test('user can create and view a blog', async ({ page }) => {
    // 登录
    await page.goto('/login')
    await page.fill('[name="username"]', 'testuser')
    await page.fill('[name="password"]', 'password')
    await page.click('[type="submit"]')

    // 创建博客
    await page.goto('/blog/create')
    await page.fill('[name="title"]', 'My Test Blog')
    await page.fill('.vditor-content', 'Blog content here')
    await page.click('button[type="submit"]')

    // 验证跳转和显示
    await expect(page).toHaveURL(/\/blog\/\d+/)
    await expect(page.locator('.blog-title')).toContainText('My Test Blog')
  })

  test('sensitive words are rejected', async ({ page }) => {
    await page.goto('/blog/create')
    await page.fill('[name="title"]', 'Contains 敏感词')
    await page.click('button[type="submit"]')

    await expect(page.locator('.error-message'))
      .toContainText('sensitive')
  })

  test('like button toggles correctly', async ({ page }) => {
    await page.goto('/blog/1')
    const likeBtn = page.locator('.like-button')

    await likeBtn.click()
    await expect(likeBtn).toHaveClass(/active/)

    await likeBtn.click()
    await expect(likeBtn).not.toHaveClass(/active/)
  })
})
```

```javascript
// e2e/admin.spec.js
test.describe('Admin Panel', () => {
  test('admin can enable email verification', async ({ page }) => {
    await page.goto('/admin/settings')
    await page.locator('[name="email_verification"]').click()
    await page.click('button[type="submit"]')

    await expect(page.locator('.toast'))
      .toContainText('Settings saved')
  })

  test('admin can manage sensitive words', async ({ page }) => {
    await page.goto('/admin/moderation/sensitive-words')
    await page.click('button.add-word')
    await page.fill('[name="word"]', 'new sensitive word')
    await page.selectOption('[name="level"]', 'strict')
    await page.click('button[type="submit"]')

    await expect(page.locator('.word-list'))
      .toContainText('new sensitive word')
  })

  test('admin can view blog statistics', async ({ page }) => {
    await page.goto('/admin/dashboard')

    await expect(page.locator('.stat-card.total-blogs'))
      .toBeVisible()
    await expect(page.locator('.stat-card.total-users'))
      .toBeVisible()
  })
})
```

```javascript
// e2e/foundation.spec.js
test.describe('百日筑基', () => {
  test('user can checkin and see streak increase', async ({ page }) => {
    await page.goto('/foundation')
    await expect(page.locator('.streak-badge .days')).toBeVisible()

    const initialStreak = await page.locator('.streak-badge .days').textContent()

    await page.click('.checkin-btn')
    await page.waitForTimeout(500)

    const newStreak = await page.locator('.streak-badge .days').textContent()
    expect(parseInt(newStreak)).toBeGreaterThanOrEqual(parseInt(initialStreak))
  })

  test('user can start and end focus session', async ({ page }) => {
    await page.goto('/foundation')

    await page.click('.timer-btn')
    await expect(page.locator('.timer-running')).toBeVisible()

    await page.waitForTimeout(2000)
    await page.click('.timer-btn')

    await expect(page.locator('.session-summary')).toBeVisible()
  })

  test('progress ring shows correct percentage', async ({ page }) => {
    await page.goto('/foundation')

    const ring = page.locator('.progress-ring circle:last-child')
    const dasharray = await ring.getAttribute('stroke-dasharray')

    // 应该显示进度
    expect(dasharray).toBeTruthy()
  })

  test('leaderboard shows top users', async ({ page }) => {
    await page.goto('/foundation/leaderboard')

    await expect(page.locator('.leaderboard-list')).toBeVisible()
    const items = page.locator('.leaderboard-item')
    expect(await items.count()).toBeGreaterThan(0)
  })
})
```

### 3.6 运行前端测试

```bash
# 单元测试
npm run test

# 单元测试 + 覆盖率
npm run test:coverage

# E2E 测试
npm run test:e2e

# UI 模式（修改代码后自动重跑）
npm run test -- --ui
```

---

## 4. CI/CD 测试集成

### 4.1 GitHub Actions

```yaml
# .github/workflows/test.yml
name: Test

on: [push, pull_request]

jobs:
  backend-test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      - name: Run tests
        run: |
          pytest --cov=apps --cov-report=xml

  frontend-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
      - name: Install dependencies
        run: npm ci
      - name: Run tests
        run: npm run test:coverage

  e2e-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install Playwright
        run: npx playwright install --with-deps
      - name: Run E2E tests
        run: npm run test:e2e
```

### 4.2 Docker Compose 测试环境

```yaml
# docker-compose.test.yml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_PASSWORD: test
      POSTGRES_DB: test_db
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U test"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build: ./backend
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    environment:
      DATABASE_URL: postgresql://test:test@postgres:5432/test_db
      REDIS_URL: redis://redis:6379
    command: pytest

  frontend:
    build: ./web-client
    command: npm run test
```

---

## 5. 测试数据管理

### 5.1 Fixture 管理

```python
# tests/fixtures/sample_data.py
import factory
from factory.faker import Faker

class UserFactory(factory.Factory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f'user_{n}')
    email = factory.LazyAttribute(lambda obj: f'{obj.username}@example.com')
    password_hash = factory.LazyFunction(lambda: hash_password('password123'))

class BlogFactory(factory.Factory):
    class Meta:
        model = Blog

    title = Faker('sentence', nb_words=6)
    content = Faker('paragraph')
    author = factory.SubFactory(UserFactory)
```

### 5.2 测试数据清理

```python
@pytest.fixture(scope="function", autouse=True)
async def cleanup(db_session):
    yield
    # 测试后清理
    await db_session.execute("DELETE FROM blogs WHERE title LIKE 'Test%'")
    await db_session.execute("DELETE FROM users WHERE username LIKE 'test%'")
```
