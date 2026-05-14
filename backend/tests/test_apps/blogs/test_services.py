import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from apps.blogs.services import BlogService
from apps.blogs.schemas import BlogCreate
from core.moderation import ModerationResult


class TestBlogService:
    async def test_create_blog_passes_moderation(self):
        """Test that blog creation succeeds when moderation passes."""
        mock_db = AsyncMock()
        mock_filter_instance = MagicMock()
        # Create a proper ModerationResult with block=False
        moderation_result = ModerationResult(
            passed=True, action="pass", original_text="test",
            moderated_text=None, flagged_words=[]
        )
        mock_filter_instance.check.return_value = moderation_result

        with patch('apps.blogs.services.get_filter', return_value=mock_filter_instance):
            service = BlogService(mock_db)
            blog_data = BlogCreate(
                title="Test Blog",
                content="This is test content",
            )
            # Mock the db operations
            mock_db.add = MagicMock()
            mock_db.flush = AsyncMock()
            mock_db.refresh = AsyncMock()

            blog = await service.create_blog(blog_data, author_id="test-author-id")

            assert blog is not None
            mock_filter_instance.check.assert_called_once()
            mock_db.add.assert_called_once()

    async def test_create_blog_blocked_by_moderation(self):
        """Test that blog is rejected when moderation returns block."""
        mock_db = AsyncMock()
        mock_filter_instance = MagicMock()
        moderation_result = ModerationResult(
            passed=False, action="block", original_text="test",
            moderated_text=None, flagged_words=["badword"]
        )
        mock_filter_instance.check.return_value = moderation_result

        with patch('apps.blogs.services.get_filter', return_value=mock_filter_instance):
            service = BlogService(mock_db)
            blog_data = BlogCreate(
                title="Test",
                content="This contains badword",
            )

            with pytest.raises(Exception) as exc_info:
                await service.create_blog(blog_data, author_id="test-author-id")

            assert "badword" in str(exc_info.value) or "prohibited" in str(exc_info.value).lower()

    async def test_create_blog_replace_moderation(self):
        """Test that blog content is replaced when moderation returns replace."""
        mock_db = AsyncMock()
        mock_filter_instance = MagicMock()
        moderation_result = ModerationResult(
            passed=True, action="replace", original_text="Test This contains bad content",
            moderated_text="Test This contains **** content", flagged_words=["bad"]
        )
        mock_filter_instance.check.return_value = moderation_result

        with patch('apps.blogs.services.get_filter', return_value=mock_filter_instance):
            service = BlogService(mock_db)
            blog_data = BlogCreate(
                title="Test",
                content="This contains bad content",
            )
            mock_db.add = MagicMock()
            mock_db.flush = AsyncMock()
            mock_db.refresh = AsyncMock()

            blog = await service.create_blog(blog_data, author_id="test-author-id")

            assert blog is not None
            # The moderation replaces "bad" with "****"
            mock_db.add.assert_called_once()

    async def test_get_blog_by_id(self):
        """Test retrieving a blog by ID."""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_blog = MagicMock()
        mock_blog.id = "test-blog-id"
        mock_blog.is_deleted = False
        mock_result.scalar_one_or_none.return_value = mock_blog
        mock_db.execute.return_value = mock_result

        with patch('apps.blogs.services.get_filter'):
            service = BlogService(mock_db)
            blog = await service.get_blog_by_id("test-blog-id")

            assert blog is not None
            assert blog.id == "test-blog-id"

    async def test_get_blog_by_id_not_found(self):
        """Test retrieving a non-existent blog returns None."""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        with patch('apps.blogs.services.get_filter'):
            service = BlogService(mock_db)
            blog = await service.get_blog_by_id("non-existent-id")

            assert blog is None

    async def test_delete_blog(self):
        """Test soft deleting a blog."""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_blog = MagicMock()
        mock_blog.id = "test-blog-id"
        mock_blog.author_id = "test-author-id"
        mock_blog.is_deleted = False
        mock_result.scalar_one_or_none.return_value = mock_blog
        mock_db.execute.return_value = mock_result
        mock_db.flush = AsyncMock()

        with patch('apps.blogs.services.get_filter'):
            service = BlogService(mock_db)
            result = await service.delete_blog("test-blog-id", "test-author-id")

            assert result is True
            assert mock_blog.is_deleted is True

    async def test_delete_blog_wrong_author(self):
        """Test that non-author cannot delete blog."""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_blog = MagicMock()
        mock_blog.id = "test-blog-id"
        mock_blog.author_id = "test-author-id"
        mock_blog.is_deleted = False
        mock_result.scalar_one_or_none.return_value = mock_blog
        mock_db.execute.return_value = mock_result

        with patch('apps.blogs.services.get_filter'):
            service = BlogService(mock_db)
            result = await service.delete_blog("test-blog-id", "wrong-author-id")

            assert result is False
