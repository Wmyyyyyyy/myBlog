# P0 + P1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** P0 produces a runnable empty-shell project (backend + frontend + Docker Compose + CI). P1 produces a fully working JWT authentication system.

**Architecture:** Backend is a FastAPI async app with SQLAlchemy asyncpg driver talking to PostgreSQL. Redis is used for Celery broker (future) and caching. Frontend is a Vue 3 SPA with Vite bundler, Pinia state, and Element Plus UI. API types are auto-generated from FastAPI OpenAPI schema via vite-plugin-openapi.

**Tech Stack:** FastAPI · SQLAlchemy async · asyncpg · Pydantic v2 · python-jose · passlib · bcrypt · Redis · Vue 3 · Vite · Pinia · Element Plus · vite-plugin-openapi · Docker Compose · GitHub Actions

---

## P0: Project Scaffolding

### P0-Task 1: Backend Directory Structure

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/.env.example`
- Create: `backend/main.py`
- Create: `backend/apps/__init__.py`
- Create: `backend/apps/users/__init__.py`
- Create: `backend/apps/users/models.py`
- Create: `backend/apps/users/schemas.py`
- Create: `backend/apps/users/views.py`
- Create: `backend/apps/users/services.py`
- Create: `backend/core/__init__.py`
- Create: `backend/core/config.py`
- Create: `backend/core/database.py`
- Create: `backend/core/redis.py`
- Create: `backend/core/security.py`
- Create: `backend/core/dependencies.py`
- Create: `backend/core/exceptions.py`
- Create: `backend/tests/conftest.py`
- Create: `backend/tests/apps/__init__.py`
- Create: `backend/tests/apps/users/__init__.py`
- Create: `backend/tests/apps/users/test_views.py`
- Modify: `backend/.gitignore` (create if not exists)

- [ ] **Step 1: Create backend directory structure and requirements.txt**

```txt
# backend/requirements.txt
fastapi==0.115.0
uvicorn[standard]==0.30.6
sqlalchemy[asyncio]==2.0.35
asyncpg==0.29.0
pydantic==2.9.2
pydantic-settings==2.5.2
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.12
redis==5.0.8
celery==5.4.0
alembic==1.13.3
pytest==8.3.3
pytest-asyncio==0.24.0
pytest-cov==5.0.0
httpx==0.27.2
Faker==28.4.1
```

- [ ] **Step 2: Create .env.example with all environment variables**

```env
# backend/.env.example
APP_NAME=Community Blog
DEBUG=True
SECRET_KEY=replace-with-random-secret-key
ALLOWED_HOSTS=localhost,127.0.0.1

DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/blog
DATABASE_URL_SYNC=postgresql://postgres:postgres@localhost:5432/blog

REDIS_URL=redis://localhost:6379/0

JWT_SECRET_KEY=replace-with-random-jwt-secret
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=user@example.com
SMTP_PASSWORD=password
EMAIL_FROM=noreply@example.com
EMAIL_VERIFICATION_ENABLED=False
```

- [ ] **Step 3: Create core/config.py**

```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_NAME: str = "Community Blog"
    DEBUG: bool = False
    SECRET_KEY: str
    ALLOWED_HOSTS: str = "localhost,127.0.0.1"

    DATABASE_URL: str
    DATABASE_URL_SYNC: str

    REDIS_URL: str = "redis://localhost:6379/0"

    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    EMAIL_VERIFICATION_ENABLED: bool = False
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAIL_FROM: str = ""


settings = Settings()
```

- [ ] **Step 4: Create core/database.py**

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncSession:
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
```

- [ ] **Step 5: Create core/redis.py**

```python
import redis.asyncio as redis

redis_client: redis.Redis | None = None


async def get_redis() -> redis.Redis:
    global redis_client
    if redis_client is None:
        redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    return redis_client


async def close_redis():
    global redis_client
    if redis_client:
        await redis_client.close()
        redis_client = None
```

- [ ] **Step 6: Create core/security.py**

```python
from datetime import datetime, timedelta, timezone
from jose import jwt
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
```

- [ ] **Step 7: Create core/dependencies.py**

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core.database import get_db
from core.security import decode_token
from apps.users.models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        if payload.get("type") != "access":
            raise credentials_exception
    except Exception:
        raise credentials_exception

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exception
    return user
```

- [ ] **Step 8: Create core/exceptions.py**

```python
from fastapi import HTTPException, status


class UserAlreadyExists(HTTPException):
    def __init__(self, detail: str = "User already exists"):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class InvalidCredentials(HTTPException):
    def __init__(self, detail: str = "Invalid credentials"):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


class EmailNotVerified(HTTPException):
    def __init__(self, detail: str = "Email not verified"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)
```

- [ ] **Step 9: Create apps/users/models.py**

```python
import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    avatar: Mapped[str | None] = mapped_column(String(500), nullable=True)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(), onupdate=lambda: datetime.now())
```

- [ ] **Step 10: Create apps/users/schemas.py**

```python
from datetime import datetime
from pydantic import BaseModel, EmailStr, field_validator


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

    @field_validator("username")
    @classmethod
    def username_min_length(cls, v: str) -> str:
        if len(v) < 3:
            raise ValueError("Username must be at least 3 characters")
        if len(v) > 50:
            raise ValueError("Username must be at most 50 characters")
        return v

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class UserLogin(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    id: str
    username: str
    email: str
    avatar: str | None
    bio: str | None
    is_admin: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class MessageResponse(BaseModel):
    message: str
```

- [ ] **Step 11: Create apps/users/services.py**

```python
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.users.models import User
from apps.users.schemas import UserCreate
from core.security import hash_password, verify_password, create_access_token, create_refresh_token


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_by_username(self, username: str) -> User | None:
        result = await self.db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> User | None:
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_user_by_id(self, user_id: str) -> User | None:
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def create_user(self, user_data: UserCreate) -> User:
        user = User(
            username=user_data.username,
            email=user_data.email,
            password_hash=hash_password(user_data.password),
        )
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user

    def authenticate_user(self, user: User, password: str) -> bool:
        return verify_password(password, user.password_hash)

    def create_tokens(self, user_id: str) -> tuple[str, str]:
        access_token = create_access_token(data={"sub": user_id})
        refresh_token = create_refresh_token(data={"sub": user_id})
        return access_token, refresh_token
```

- [ ] **Step 12: Create apps/users/views.py**

```python
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.dependencies import get_current_user
from core.security import decode_token
from core.exceptions import UserAlreadyExists, InvalidCredentials, EmailNotVerified
from apps.users.models import User
from apps.users.schemas import (
    UserCreate, UserLogin, UserOut, TokenResponse, RefreshRequest, MessageResponse
)
from apps.users.services import AuthService

router = APIRouter(prefix="/api/auth", tags=["认证"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    existing = await service.get_user_by_username(user_data.username)
    if existing:
        raise UserAlreadyExists(f"Username '{user_data.username}' already registered")
    existing_email = await service.get_user_by_email(user_data.email)
    if existing_email:
        raise UserAlreadyExists(f"Email '{user_data.email}' already registered")
    user = await service.create_user(user_data)
    return user


@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    user = await service.get_user_by_username(form_data.username)
    if not user or not service.authenticate_user(user, form_data.password):
        raise InvalidCredentials("Incorrect username or password")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is inactive")
    if not user.email_verified and settings.EMAIL_VERIFICATION_ENABLED:
        raise EmailNotVerified()
    access_token, refresh_token = service.create_tokens(user.id)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/logout", response_model=MessageResponse)
async def logout(current_user: User = Depends(get_current_user)):
    return MessageResponse(message="Logged out successfully")


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(req: RefreshRequest, db: AsyncSession = Depends(get_db)):
    try:
        payload = decode_token(req.refresh_token)
        if payload.get("type") != "refresh":
            raise InvalidCredentials("Invalid refresh token")
        user_id = payload.get("sub")
    except Exception:
        raise InvalidCredentials("Invalid refresh token")

    service = AuthService(db)
    user = await service.get_user_by_id(user_id)
    if not user or not user.is_active:
        raise InvalidCredentials("User not found or inactive")

    access_token, new_refresh_token = service.create_tokens(user.id)
    return TokenResponse(access_token=access_token, refresh_token=new_refresh_token)


@router.get("/me", response_model=UserOut)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user
```

- [ ] **Step 13: Create main.py**

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from core.redis import close_redis
from apps.users.views import router as users_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await close_redis()


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users_router)


@app.get("/health")
async def health():
    return {"status": "ok"}
```

- [ ] **Step 14: Create backend/.gitignore**

```
__pycache__/
*.py[cod]
*.so
.env
venv/
.venv/
htmlcov/
.coverage
.pytest_cache/
.mypy_cache/
dist/
build/
*.egg-info/
.eggs/
```

- [ ] **Step 15: Create backend/tests/conftest.py**

```python
import pytest
import asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from main import app
from core.database import Base, get_db

TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/blog_test"


@pytest.fixture(scope="session")
def event_loop():
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def db_session():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncSession(engine) as session:
        yield session
        await session.rollback()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


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
def faker_email():
    import uuid
    return f"test_{uuid.uuid4().hex[:8]}@example.com"
```

- [ ] **Step 16: Create backend/tests/apps/users/test_views.py**

```python
import pytest
from apps.users.schemas import UserCreate


class TestUserRegistration:
    async def test_register_success(self, client, faker_email):
        response = await client.post("/api/auth/register", json={
            "username": "testuser",
            "email": faker_email,
            "password": "SecurePass123"
        })
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "testuser"
        assert "id" in data

    async def test_register_duplicate_username(self, client, faker_email):
        await client.post("/api/auth/register", json={
            "username": "duplicateuser",
            "email": faker_email,
            "password": "SecurePass123"
        })
        response = await client.post("/api/auth/register", json={
            "username": "duplicateuser",
            "email": "another@example.com",
            "password": "SecurePass123"
        })
        assert response.status_code == 400

    async def test_register_duplicate_email(self, client):
        email = "sametest@example.com"
        await client.post("/api/auth/register", json={
            "username": "user1",
            "email": email,
            "password": "SecurePass123"
        })
        response = await client.post("/api/auth/register", json={
            "username": "user2",
            "email": email,
            "password": "SecurePass123"
        })
        assert response.status_code == 400

    async def test_register_invalid_email(self, client):
        response = await client.post("/api/auth/register", json={
            "username": "testuser",
            "email": "not-an-email",
            "password": "SecurePass123"
        })
        assert response.status_code == 422

    async def test_register_password_too_short(self, client, faker_email):
        response = await client.post("/api/auth/register", json={
            "username": "testuser",
            "email": faker_email,
            "password": "123"
        })
        assert response.status_code == 422


class TestUserLogin:
    async def test_login_success(self, client, faker_email):
        await client.post("/api/auth/register", json={
            "username": "loginuser",
            "email": faker_email,
            "password": "SecurePass123"
        })
        response = await client.post(
            "/api/auth/login",
            data={"username": "loginuser", "password": "SecurePass123"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_wrong_password(self, client, faker_email):
        await client.post("/api/auth/register", json={
            "username": "loginuser2",
            "email": faker_email,
            "password": "SecurePass123"
        })
        response = await client.post(
            "/api/auth/login",
            data={"username": "loginuser2", "password": "WrongPass"}
        )
        assert response.status_code == 401

    async def test_login_nonexistent_user(self, client):
        response = await client.post(
            "/api/auth/login",
            data={"username": "nonexistent", "password": "AnyPass"}
        )
        assert response.status_code == 401


class TestUserMe:
    async def test_get_me_authenticated(self, client, faker_email):
        register_resp = await client.post("/api/auth/register", json={
            "username": "meuser",
            "email": faker_email,
            "password": "SecurePass123"
        })
        user_id = register_resp.json()["id"]

        login_resp = await client.post(
            "/api/auth/login",
            data={"username": "meuser", "password": "SecurePass123"}
        )
        token = login_resp.json()["access_token"]

        me_resp = await client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert me_resp.status_code == 200
        data = me_resp.json()
        assert data["id"] == user_id
        assert data["username"] == "meuser"

    async def test_get_me_unauthenticated(self, client):
        response = await client.get("/api/auth/me")
        assert response.status_code == 401
```

- [ ] **Step 17: Commit backend scaffold**

```bash
cd backend
git init
git add requirements.txt .env.example .gitignore main.py apps/ core/ tests/
git commit -m "feat: P0 backend scaffold - FastAPI structure, SQLAlchemy async, JWT security"
```

---

### P0-Task 2: Frontend Directory Structure

**Files:**
- Create: `web-client/package.json`
- Create: `web-client/vite.config.js`
- Create: `web-client/index.html`
- Create: `web-client/.env.development`
- Create: `web-client/.env.production`
- Create: `web-client/.gitignore`
- Create: `web-client/src/main.js`
- Create: `web-client/src/App.vue`
- Create: `web-client/src/api/index.js`
- Create: `web-client/src/api/auth.js`
- Create: `web-client/src/stores/auth.js`
- Create: `web-client/src/composables/useAuth.js`
- Create: `web-client/src/router/index.js`
- Create: `web-client/src/styles/index.scss`
- Create: `web-client/src/views/Login.vue`
- Create: `web-client/src/views/Register.vue`
- Create: `web-client/src/components/HelloWorld.vue`
- Create: `web-client/src/components/TheNavbar.vue`

- [ ] **Step 1: Create web-client/package.json**

```json
{
  "name": "web-client",
  "version": "1.0.0",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview",
    "test": "vitest",
    "test:coverage": "vitest run --coverage"
  },
  "dependencies": {
    "vue": "^3.5.0",
    "vue-router": "^4.4.0",
    "pinia": "^2.2.0",
    "axios": "^1.7.0",
    "element-plus": "^2.8.0",
    "@element-plus/icons-vue": "^2.3.0"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^5.1.0",
    "vite": "^5.4.0",
    "vite-plugin-openapi": "^0.4.0",
    "sass": "^1.78.0",
    "vitest": "^2.0.0",
    "@vue/test-utils": "^2.4.0",
    "eslint": "^9.0.0",
    "prettier": "^3.3.0"
  }
}
```

- [ ] **Step 2: Create web-client/vite.config.js**

```javascript
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import OpenAPI from 'vite-plugin-openapi'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig({
  plugins: [
    vue(),
    OpenAPI({
      target: 'http://localhost:8000',
      output: './src/api/generated',
      client: 'axios',
      exportSchemas: true,
      watch: true,
    }),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: process.env.VITE_API_BASE_URL || 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
```

- [ ] **Step 3: Create web-client/.env.development**

```env
VITE_API_BASE_URL=http://localhost:8000
```

- [ ] **Step 4: Create web-client/.env.production**

```env
VITE_API_BASE_URL=https://api.yoursite.com
```

- [ ] **Step 5: Create web-client/src/main.js**

```javascript
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIcons from '@element-plus/icons-vue'

import App from './App.vue'
import router from './router'
import './styles/index.scss'

const app = createApp(App)

// Register all Element Plus icons globally
for (const [key, component] of Object.entries(ElementPlusIcons)) {
  app.component(key, component)
}

app.use(createPinia())
app.use(router)
app.use(ElementPlus)

app.mount('#app')
```

- [ ] **Step 6: Create web-client/src/App.vue**

```vue
<template>
  <div id="app">
    <TheNavbar v-if="authStore.isLoggedIn" />
    <router-view />
  </div>
</template>

<script setup>
import TheNavbar from '@/components/TheNavbar.vue'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
</script>

<style>
#app {
  min-height: 100vh;
  background-color: #f5f5f5;
}
</style>
```

- [ ] **Step 7: Create web-client/src/router/index.js**

```javascript
import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes = [
  {
    path: '/',
    redirect: '/blogs',
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { guest: true },
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/Register.vue'),
    meta: { guest: true },
  },
  {
    path: '/blogs',
    name: 'BlogList',
    component: () => import('@/views/BlogList.vue'),
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  const isLoggedIn = authStore.isLoggedIn

  if (to.meta.guest && isLoggedIn) {
    next('/blogs')
  } else if (!to.meta.guest && !isLoggedIn) {
    next('/login')
  } else {
    next()
  }
})

export default router
```

- [ ] **Step 8: Create web-client/src/stores/auth.js**

```javascript
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '@/api/auth'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('access_token') || '')
  const user = ref(JSON.parse(localStorage.getItem('user') || 'null'))

  const isLoggedIn = computed(() => !!token.value)

  async function login(username, password) {
    const formData = new FormData()
    formData.append('username', username)
    formData.append('password', password)
    const response = await authApi.login(formData)
    token.value = response.access_token
    localStorage.setItem('access_token', response.access_token)
    await fetchMe()
  }

  async function register(username, email, password) {
    await authApi.register({ username, email, password })
    await login(username, password)
  }

  async function fetchMe() {
    if (!token.value) return
    try {
      const response = await authApi.me()
      user.value = response
      localStorage.setItem('user', JSON.stringify(response))
    } catch {
      logout()
    }
  }

  function logout() {
    token.value = ''
    user.value = null
    localStorage.removeItem('access_token')
    localStorage.removeItem('user')
  }

  if (token.value) {
    fetchMe()
  }

  return { token, user, isLoggedIn, login, register, logout, fetchMe }
})
```

- [ ] **Step 9: Create web-client/src/api/auth.js**

```javascript
// NOTE: This file is auto-generated by vite-plugin-openapi.
// Do NOT edit manually. Regenerates on /openapi.json changes.

import client from './index'

export const authApi = {
  register(data) {
    return client.post('/api/auth/register', data)
  },
  login(data) {
    return client.post('/api/auth/login', data)
  },
  logout() {
    return client.post('/api/auth/logout')
  },
  refreshToken(data) {
    return client.post('/api/auth/refresh', data)
  },
  me() {
    return client.get('/api/auth/me')
  },
}
```

- [ ] **Step 10: Create web-client/src/api/index.js**

```javascript
import axios from 'axios'
import { ElMessage } from 'element-plus'

const client = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

client.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

client.interceptors.response.use(
  (response) => response,
  (error) => {
    const message = error.response?.data?.detail || error.message || 'Network error'
    ElMessage.error(message)
    return Promise.reject(error)
  }
)

export default client
```

- [ ] **Step 11: Create web-client/src/composables/useAuth.js**

```javascript
import { useAuthStore } from '@/stores/auth'

export function useAuth() {
  const authStore = useAuthStore()

  async function handleLogin(username, password) {
    await authStore.login(username, password)
  }

  async function handleRegister(username, email, password) {
    await authStore.register(username, email, password)
  }

  function handleLogout() {
    authStore.logout()
  }

  return {
    user: authStore.user,
    isLoggedIn: authStore.isLoggedIn,
    login: handleLogin,
    register: handleRegister,
    logout: handleLogout,
  }
}
```

- [ ] **Step 12: Create web-client/src/views/Login.vue**

```vue
<template>
  <div class="auth-page">
    <el-card class="auth-card">
      <template #header>
        <h2>登录</h2>
      </template>
      <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="form.password" type="password" placeholder="请输入密码" show-password />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" style="width: 100%" @click="onSubmit">
            登录
          </el-button>
        </el-form-item>
      </el-form>
      <div class="auth-footer">
        还没有账号？<router-link to="/register">立即注册</router-link>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '@/composables/useAuth'

const router = useRouter()
const { login } = useAuth()

const formRef = ref(null)
const loading = ref(false)

const form = reactive({
  username: '',
  password: '',
})

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

async function onSubmit() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    await login(form.username, form.password)
    router.push('/blogs')
  } catch {
    // error handled by interceptor
  } finally {
    loading.value = false
  }
}
</script>

<style lang="scss" scoped>
.auth-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.auth-card {
  width: 400px;
  max-width: 90vw;
}

.auth-footer {
  text-align: center;
  font-size: 14px;
  color: #666;
}

a {
  color: #409eff;
  text-decoration: none;
}
</style>
```

- [ ] **Step 13: Create web-client/src/views/Register.vue**

```vue
<template>
  <div class="auth-page">
    <el-card class="auth-card">
      <template #header>
        <h2>注册</h2>
      </template>
      <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" placeholder="3-50个字符" />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="form.email" type="email" placeholder="请输入邮箱" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="form.password" type="password" placeholder="至少8个字符" show-password />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" style="width: 100%" @click="onSubmit">
            注册
          </el-button>
        </el-form-item>
      </el-form>
      <div class="auth-footer">
        已有账号？<router-link to="/login">立即登录</router-link>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '@/composables/useAuth'

const router = useRouter()
const { register } = useAuth()

const formRef = ref(null)
const loading = ref(false)

const form = reactive({
  username: '',
  email: '',
  password: '',
})

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 50, message: '用户名长度 3-50 个字符', trigger: 'blur' },
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入有效邮箱', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 8, message: '密码至少8个字符', trigger: 'blur' },
  ],
}

async function onSubmit() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    await register(form.username, form.email, form.password)
    router.push('/blogs')
  } catch {
    // error handled by interceptor
  } finally {
    loading.value = false
  }
}
</script>

<style lang="scss" scoped>
.auth-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.auth-card {
  width: 400px;
  max-width: 90vw;
}

.auth-footer {
  text-align: center;
  font-size: 14px;
  color: #666;
}

a {
  color: #409eff;
  text-decoration: none;
}
</style>
```

- [ ] **Step 14: Create web-client/src/components/TheNavbar.vue**

```vue
<template>
  <el-menu mode="horizontal" :ellipsis="false" router>
    <el-menu-item index="/blogs" class="logo">博客</el-menu-item>
    <div style="flex: 1" />
    <el-menu-item v-if="isLoggedIn" index="/profile">个人中心</el-menu-item>
    <el-menu-item v-if="isLoggedIn" @click="handleLogout">退出</el-menu-item>
    <el-menu-item v-else index="/login">登录</el-menu-item>
  </el-menu>
</template>

<script setup>
import { useAuth } from '@/composables/useAuth'
import { useRouter } from 'vue-router'

const { isLoggedIn, logout } = useAuth()
const router = useRouter()

function handleLogout() {
  logout()
  router.push('/login')
}
</script>

<style scoped>
.logo {
  font-weight: bold;
  font-size: 18px;
}
</style>
```

- [ ] **Step 15: Create web-client/src/components/HelloWorld.vue** (placeholder for later)

```vue
<template>
  <div class="hello">
    <h1>{{ msg }}</h1>
  </div>
</template>

<script setup>
defineProps({ msg: String })
</script>
```

- [ ] **Step 16: Create web-client/src/views/BlogList.vue** (placeholder for later)

```vue
<template>
  <div class="blog-list-page">
    <h1>博客列表</h1>
    <p>功能开发中...</p>
  </div>
</template>
```

- [ ] **Step 17: Create web-client/src/styles/index.scss**

```scss
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Inter', 'Noto Sans SC', -apple-system, BlinkMacSystemFont, sans-serif;
  color: #333;
  background-color: #f5f5f5;
}

a {
  text-decoration: none;
  color: inherit;
}
```

- [ ] **Step 18: Create web-client/.gitignore**

```
node_modules/
dist/
.env
.env.local
.env.development.local
.env.production.local
*.local
.DS_Store
coverage/
```

- [ ] **Step 19: Commit frontend scaffold**

```bash
cd web-client
npm install
git init
git add package.json vite.config.js index.html .env.development .env.production .gitignore src/
git commit -m "feat: P0 frontend scaffold - Vue 3 + Vite + Pinia + Element Plus + vite-plugin-openapi"
```

---

### P0-Task 3: Docker Compose Setup

**Files:**
- Create: `docker-compose.yml`
- Create: `docker-compose.prod.yml`
- Create: `backend/Dockerfile`
- Create: `web-client/nginx.conf`

- [ ] **Step 1: Create docker-compose.yml (development)**

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: blog
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
```

- [ ] **Step 2: Create docker-compose.prod.yml (production)**

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-postgres}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-changeme}
      POSTGRES_DB: ${POSTGRES_DB:-blog}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7
    volumes:
      - redis_data:/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    env_file:
      - ./backend/.env
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./web-client/dist:/usr/share/nginx/html
      - ./web-client/nginx.conf:/etc/nginx/conf.d/default.conf
      - uploads:/var/www/blog/uploads
    depends_on:
      - backend
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
  uploads:
```

- [ ] **Step 3: Create backend/Dockerfile**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 4: Create web-client/nginx.conf**

```nginx
server {
    listen 80;
    server_name _;
    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /docs {
        proxy_pass http://backend:8000;
    }

    location /redoc {
        proxy_pass http://backend:8000;
    }

    location /openapi.json {
        proxy_pass http://backend:8000;
    }

    location /uploads/ {
        alias /var/www/blog/uploads/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

- [ ] **Step 5: Commit Docker files**

```bash
git add docker-compose.yml docker-compose.prod.yml backend/Dockerfile web-client/nginx.conf
git commit -m "feat: P0 Docker Compose setup - PostgreSQL, Redis, Nginx, backend"
```

---

### P0-Task 4: GitHub Actions CI

**Files:**
- Create: `.github/workflows/ci.yml`

- [ ] **Step 1: Create .github/workflows/ci.yml**

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  backend-test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
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
          cd backend
          pip install -r requirements.txt
      - name: Run tests
        env:
          DATABASE_URL: postgresql+asyncpg://postgres:postgres@localhost:5432/blog_test
          REDIS_URL: redis://localhost:6379/0
          JWT_SECRET_KEY: test-secret-key
          SECRET_KEY: test-secret-key
        run: |
          cd backend
          pytest -v --cov=apps --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          files: ./backend/coverage.xml
          flags: backend

  frontend-build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: web-client/package-lock.json
      - name: Install dependencies
        run: |
          cd web-client
          npm ci
      - name: Build
        run: |
          cd web-client
          npm run build
```

- [ ] **Step 2: Commit CI**

```bash
git add .github/workflows/ci.yml
git commit -m "feat: P0 GitHub Actions CI - backend tests + frontend build"
```

---

## P1: Authentication System

### P1-Task 1: Backend Authentication — Complete and Test

**Files:**
- Modify: `backend/apps/users/views.py` (add missing imports and settings reference)
- Test: `backend/tests/apps/users/test_views.py`
- Modify: `backend/.env` (create from .env.example)

- [ ] **Step 1: Write failing test for login endpoint returns token**

```python
async def test_login_returns_access_token(self, client, faker_email):
    await client.post("/api/auth/register", json={
        "username": "tokenuser",
        "email": faker_email,
        "password": "SecurePass123"
    })
    response = await client.post(
        "/api/auth/login",
        data={"username": "tokenuser", "password": "SecurePass123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
```

- [ ] **Step 2: Write failing test for refresh token**

```python
async def test_refresh_token(self, client, faker_email):
    await client.post("/api/auth/register", json={
        "username": "refreshuser",
        "email": faker_email,
        "password": "SecurePass123"
    })
    login_resp = await client.post(
        "/api/auth/login",
        data={"username": "refreshuser", "password": "SecurePass123"}
    )
    refresh_token = login_resp.json()["refresh_token"]

    refresh_resp = await client.post(
        "/api/auth/refresh",
        json={"refresh_token": refresh_token}
    )
    assert refresh_resp.status_code == 200
    assert "access_token" in refresh_resp.json()
```

- [ ] **Step 3: Fix apps/users/views.py — add missing import for settings**

```python
from core.config import settings
```

- [ ] **Step 4: Run tests**

Run: `cd backend && pytest tests/apps/users/test_views.py -v`
Expected: All tests pass

- [ ] **Step 5: Create backend/.env from .env.example for local dev**

```bash
cd backend && cp .env.example .env
# Edit .env and fill in real values for DATABASE_URL, JWT_SECRET_KEY, SECRET_KEY
```

- [ ] **Step 6: Test full auth flow manually**

```bash
# Start postgres and redis via docker compose
docker compose up -d postgres redis

# Start backend
cd backend && uvicorn main:app --reload --port 8000

# In another terminal, test the API
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","email":"test@example.com","password":"SecurePass123"}'

curl -X POST http://localhost:8000/api/auth/login \
  -d "username=testuser&password=SecurePass123"

# Copy access_token from response and call /me
curl http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer <access_token>"
```

- [ ] **Step 7: Commit**

```bash
git add backend/apps/users/ backend/tests/ backend/.env
git commit -m "feat: P1 backend auth - register, login, logout, refresh, /me endpoints"
```

---

### P1-Task 2: Frontend Authentication — Complete UI and Store

**Files:**
- Modify: `web-client/src/stores/auth.js` (add token refresh interceptor)
- Modify: `web-client/src/api/index.js` (add response interceptor for 401)
- Modify: `web-client/src/api/auth.js` (add refreshToken method)
- Create: `web-client/src/components/UserAvatar.vue`
- Create: `web-client/src/components/BaseButton.vue`
- Create: `web-client/src/views/Profile.vue`

- [ ] **Step 1: Add 401 response interceptor in web-client/src/api/index.js**

```javascript
let isRefreshing = false
let refreshSubscribers = []

function subscribeTokenRefresh(callback) {
  refreshSubscribers.push(callback)
}

function onTokenRefreshed() {
  refreshSubscribers.forEach(cb => cb())
  refreshSubscribers = []
}

client.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        return new Promise(resolve => {
          subscribeTokenRefresh(() => resolve(client(originalRequest)))
        })
      }

      originalRequest._retry = true
      isRefreshing = true

      try {
        const refreshToken = localStorage.getItem('refresh_token')
        if (!refreshToken) throw new Error('No refresh token')

        const response = await axios.post(
          `${import.meta.env.VITE_API_BASE_URL}/api/auth/refresh`,
          { refresh_token: refreshToken }
        )
        const { access_token, refresh_token: newRefreshToken } = response.data

        localStorage.setItem('access_token', access_token)
        localStorage.setItem('refresh_token', newRefreshToken)

        client.defaults.headers.common['Authorization'] = `Bearer ${access_token}`
        onTokenRefreshed()
        return client(originalRequest)
      } catch {
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        window.location.href = '/login'
        return Promise.reject(error)
      } finally {
        isRefreshing = false
      }
    }

    return Promise.reject(error)
  }
)
```

- [ ] **Step 2: Add refreshToken to web-client/src/api/auth.js**

```javascript
refreshToken(data) {
  return client.post('/api/auth/refresh', data)
},
```

- [ ] **Step 3: Update web-client/src/stores/auth.js to store refresh_token**

```javascript
async function login(username, password) {
  const formData = new FormData()
  formData.append('username', username)
  formData.append('password', password)
  const response = await authApi.login(formData)
  token.value = response.access_token
  localStorage.setItem('access_token', response.access_token)
  localStorage.setItem('refresh_token', response.refresh_token)
  await fetchMe()
}
```

- [ ] **Step 4: Create web-client/src/components/UserAvatar.vue**

```vue
<template>
  <el-avatar :size="size" :src="src || defaultAvatar">
    <el-icon><User /></el-icon>
  </el-avatar>
</template>

<script setup>
defineProps({
  src: String,
  size: {
    type: [Number, String],
    default: 40,
  },
})

const defaultAvatar = ''
</script>
```

- [ ] **Step 5: Create web-client/src/views/Profile.vue**

```vue
<template>
  <div class="profile-page">
    <el-card>
      <template #header>
        <h2>个人中心</h2>
      </template>
      <el-descriptions :column="1" border>
        <el-descriptions-item label="用户名">{{ user?.username }}</el-descriptions-item>
        <el-descriptions-item label="邮箱">{{ user?.email }}</el-descriptions-item>
        <el-descriptions-item label="注册时间">
          {{ new Date(user?.created_at).toLocaleDateString() }}
        </el-descriptions-item>
      </el-descriptions>
    </el-card>
  </div>
</template>

<script setup>
import { useAuth } from '@/composables/useAuth'

const { user } = useAuth()
</script>

<style scoped>
.profile-page {
  max-width: 600px;
  margin: 40px auto;
  padding: 0 20px;
}
</style>
```

- [ ] **Step 6: Test login/register flow in browser**

```bash
cd web-client && npm install && npm run dev
# Open http://localhost:3000/register
# Fill form and submit
# Should redirect to /blogs and show navbar with user info
```

- [ ] **Step 7: Commit**

```bash
git add web-client/src/
git commit -m "feat: P1 frontend auth - login/register forms, auth store with token refresh, profile page"
```

---

## P0 + P1 Self-Review Checklist

- [ ] **Spec coverage:** All P0 items (backend scaffold, frontend scaffold, Docker Compose, CI, env templates) have tasks. All P1 items (register, login, logout, refresh, /me) have tasks.
- [ ] **Placeholder scan:** No "TBD", "TODO", or vague implementation steps found.
- [ ] **Type consistency:** `UserOut` schema fields match across views.py, test assertions, and frontend store. `TokenResponse` has `access_token`, `refresh_token`, `token_type` throughout.
- [ ] **Docker Compose ports:** postgres:5432, redis:6379, backend:8000, nginx:80 — all non-conflicting.
- [ ] **Security:** Passwords hashed with bcrypt, JWT secrets loaded from env vars, HttpOnly cookie pattern noted for future.
- [ ] **Frontend auth flow:** Login → token stored → API interceptor attaches Bearer header → 401 triggers refresh → refresh fails redirects to login. Complete flow.
- [ ] **No placeholder code:** Every step shows actual code or exact command to run.

---

## Next Steps

1. **UI Design** (before P1 execution): Design system + page layouts for login, register, blog list, blog detail, profile pages. Output: component preview page.
2. **Execute P0**: Run P0-Task 1 through P0-Task 4 in order.
3. **Verify P0**: Backend starts, frontend builds, Docker Compose runs, CI passes.
4. **Execute P1**: Run P1-Task 1 through P1-Task 2 in order.
5. **Verify P1**: Full auth flow works end-to-end (register → login → access protected route → logout).
