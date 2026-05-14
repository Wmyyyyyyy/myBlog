"""
初始化数据库表 + 创建管理员账户
"""
import asyncio
import sys
import uuid
from datetime import datetime
import bcrypt

sys.path.insert(0, '.')

from core.database import engine, Base, AsyncSessionLocal
from apps.users.models import User
from apps.blogs.models import Blog
from apps.comments.models import Comment
from apps.interactions.models import Favorite, Like, Follow
from apps.dynamics.models import DynamicEvent
from apps.foundation.models import CheckIn, Achievement
from apps.admin.models import AdminLog, LoginLog, IPBan


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


async def init_tables():
    """创建所有表"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    print("All tables created successfully!")


async def create_admin_user():
    """创建管理员账户"""
    async with AsyncSessionLocal() as session:
        from sqlalchemy import select
        result = await session.execute(select(User).where(User.username == "admin"))
        existing = result.scalar_one_or_none()

        if existing:
            print("Admin user already exists!")
            if not existing.is_admin:
                existing.is_admin = True
                await session.commit()
                print("Updated existing user to admin.")
            return

        admin = User(
            id=str(uuid.uuid4()),
            username="admin",
            email="admin@myblog.com",
            password_hash=hash_password("admin123456"),
            is_admin=True,
            is_active=True,
            created_at=datetime.now(),
        )
        session.add(admin)
        await session.commit()
        print("Admin user created!")
        print("  Username: admin")
        print("  Password: admin123456")
        print("  (请登录后立即修改密码!)")


async def main():
    print("=" * 50)
    print("Initializing database...")
    print("=" * 50)

    await init_tables()
    await create_admin_user()

    print("=" * 50)
    print("Done!")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
