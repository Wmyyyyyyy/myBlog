import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from apps.dynamics.services import DynamicService
from apps.dynamics.models import DynamicEvent


class TestDynamicService:
    @pytest.fixture
    def mock_db(self):
        db = AsyncMock()
        db.add = MagicMock()
        db.flush = AsyncMock()
        db.refresh = AsyncMock()
        return db

    @pytest.fixture
    def service(self, mock_db):
        return DynamicService(mock_db)

    @pytest.mark.asyncio
    async def test_create_event(self, service, mock_db):
        """Test basic event creation"""
        result = await service.create_event(
            user_id="user-123",
            event_type="blog_post",
            target_id="blog-456",
            target_user_id="author-789",
            target_title="Test Blog Title",
        )

        assert result.user_id == "user-123"
        assert result.event_type == "blog_post"
        assert result.target_id == "blog-456"
        assert result.target_user_id == "author-789"
        assert result.target_title == "Test Blog Title"
        mock_db.add.assert_called_once()
        mock_db.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_record_blog_post(self, service, mock_db):
        """Test recording a blog post event"""
        mock_blog = MagicMock()
        mock_blog.id = "blog-123"
        mock_blog.author_id = "user-456"
        mock_blog.title = "My Test Blog"

        result = await service.record_blog_post(mock_blog)

        assert result.user_id == "user-456"
        assert result.event_type == "blog_post"
        assert result.target_id == "blog-123"
        assert result.target_title == "My Test Blog"

    @pytest.mark.asyncio
    async def test_record_like_blog(self, service, mock_db):
        """Test recording a like blog event"""
        result = await service.record_like_blog(
            user_id="liker-123",
            blog_id="blog-456",
            blog_author_id="author-789",
        )

        assert result.user_id == "liker-123"
        assert result.event_type == "like_blog"
        assert result.target_id == "blog-456"
        assert result.target_user_id == "author-789"

    @pytest.mark.asyncio
    async def test_record_favorite_blog(self, service, mock_db):
        """Test recording a favorite blog event"""
        result = await service.record_favorite_blog(
            user_id="user-123",
            blog_id="blog-456",
            blog_author_id="author-789",
        )

        assert result.user_id == "user-123"
        assert result.event_type == "favorite_blog"
        assert result.target_id == "blog-456"
        assert result.target_user_id == "author-789"

    @pytest.mark.asyncio
    async def test_record_follow(self, service, mock_db):
        """Test recording a follow event"""
        result = await service.record_follow(
            follower_id="user-123",
            following_id="user-456",
        )

        assert result.user_id == "user-123"
        assert result.event_type == "follow_user"
        assert result.target_id == "user-456"
        assert result.target_user_id == "user-456"

    @pytest.mark.asyncio
    async def test_record_checkin(self, service, mock_db):
        """Test recording a checkin event"""
        result = await service.record_checkin(
            user_id="user-123",
            achievement_id="ach-456",
            achievement_name="7-Day Streak",
        )

        assert result.user_id == "user-123"
        assert result.event_type == "checkin"
        assert result.target_id == "ach-456"
        assert result.target_title == "7-Day Streak"

    @pytest.mark.asyncio
    async def test_get_user_feed_empty(self, service, mock_db):
        """Test getting user feed when no following"""
        # Mock empty follow result
        mock_result = MagicMock()
        mock_result.fetchall = MagicMock(return_value=[])
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await service.get_user_feed(user_id="user-123", limit=20)

        assert result.events == []
        assert result.next_cursor is None

    @pytest.mark.asyncio
    async def test_get_user_events_empty(self, service, mock_db):
        """Test getting user events when none exist"""
        mock_result = MagicMock()
        mock_result.scalars = MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await service.get_user_events(user_id="user-123", limit=20)

        assert result.events == []
        assert result.next_cursor is None
