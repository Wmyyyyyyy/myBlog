import os
import sys
from pathlib import Path

import pytest

# Store backend directory before pytest modifies sys.path
_backend_dir = Path(__file__).resolve().parent.parent


def pytest_configure(config):
    """Add backend directory to sys.path before test collection."""
    backend_path = str(_backend_dir)
    tests_path = str(_backend_dir / "tests")
    # Remove tests directory from sys.path to avoid shadowing the real apps module
    if tests_path in sys.path:
        sys.path.remove(tests_path)
    # Ensure backend is at position 0
    if backend_path in sys.path:
        sys.path.remove(backend_path)
    sys.path.insert(0, backend_path)

    # Set test environment variables
    os.environ.setdefault("SECRET_KEY", "test-secret-key-for-testing-only")
    os.environ.setdefault(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:qwe112233@localhost:5432/blog_test",
    )
    os.environ.setdefault(
        "DATABASE_URL_SYNC",
        "postgresql://postgres:qwe112233@localhost:5432/blog_test",
    )
    os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-testing-only")
    os.environ.setdefault("EMAIL_VERIFICATION_ENABLED", "false")


@pytest.fixture(scope="session")
def event_loop():
    import asyncio
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_engine():
    from sqlalchemy.ext.asyncio import create_async_engine

    TEST_DATABASE_URL = os.environ.get(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/blog_test",
    )

    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
    )
    return engine


@pytest.fixture(scope="function")
async def db_session(test_engine):
    from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
    from core.database import Base

    TestingSessionLocal = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestingSessionLocal() as session:
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function")
async def client(db_session):
    from httpx import AsyncClient, ASGITransport
    from main import app
    from core.database import get_db

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
def user_token():
    from core.security import create_access_token

    return create_access_token("test-user-id")


@pytest.fixture
def user_refresh_token():
    from core.security import create_refresh_token

    return create_refresh_token("test-user-id")


@pytest.fixture
def faker_email():
    import uuid

    return f"test_{uuid.uuid4().hex[:8]}@example.com"
