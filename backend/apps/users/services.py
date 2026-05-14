from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from apps.users.models import User
from apps.users.schemas import UserCreate
from core.security import verify_password, get_password_hash
from core.exceptions import UserAlreadyExists, InvalidCredentials, EmailNotVerified

class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_by_username(self, username: str) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def create_user(self, user_data: UserCreate) -> User:
        existing_user = await self.get_user_by_username(user_data.username)
        if existing_user:
            raise UserAlreadyExists("Username already registered")

        existing_email = await self.get_user_by_email(user_data.email)
        if existing_email:
            raise UserAlreadyExists("Email already registered")

        hashed_password = get_password_hash(user_data.password)

        user = User(
            username=user_data.username,
            email=user_data.email,
            password_hash=hashed_password,
        )

        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def authenticate_user(self, username: str, password: str) -> User:
        user = await self.get_user_by_username(username)
        if not user:
            raise InvalidCredentials("Invalid username or password")

        if not verify_password(password, user.password_hash):
            raise InvalidCredentials("Invalid username or password")

        if not user.is_active:
            raise InvalidCredentials("User account is inactive")

        return user

    async def verify_email(self, user: User) -> None:
        if not user.email_verified:
            raise EmailNotVerified("Email not verified")
