import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from apps.comments.services import CommentService
from apps.comments.schemas import CommentCreate
from apps.comments.models import Comment


class TestCommentService:
    @pytest.fixture
    def mock_db(self):
        db = AsyncMock()
        db.add = MagicMock()
        db.flush = AsyncMock()
        db.refresh = AsyncMock()
        return db

    @pytest.fixture
    def service(self, mock_db):
        return CommentService(mock_db)

    @pytest.mark.asyncio
    async def test_create_comment(self, service, mock_db):
        comment_data = CommentCreate(
            blog_id="blog-123",
            content="Test comment"
        )

        result = await service.create_comment(comment_data, author_id="user-123")

        assert result.blog_id == "blog-123"
        assert result.content == "Test comment"
        assert result.author_id == "user-123"
        assert result.level == 0
        assert result.parent_id is None
        assert result.root_id is None

    @pytest.mark.asyncio
    async def test_create_reply(self, service, mock_db):
        # Create parent comment
        parent_comment = Comment(
            blog_id="blog-123",
            author_id="user-123",
            content="Parent comment",
            level=0
        )
        parent_comment.id = "parent-123"

        # Mock getting parent comment
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=parent_comment)
        mock_db.execute = AsyncMock(return_value=mock_result)

        comment_data = CommentCreate(
            blog_id="blog-123",
            content="Reply comment",
            parent_id="parent-123"
        )

        result = await service.create_comment(comment_data, author_id="user-123")

        assert result.level == 1
        assert result.parent_id == "parent-123"
        assert result.root_id == "parent-123"

    @pytest.mark.asyncio
    async def test_create_reply_too_deep(self, service, mock_db):
        # Create parent comment at level 2 (max level)
        parent_comment = Comment(
            blog_id="blog-123",
            author_id="user-123",
            content="Parent at level 2",
            level=2
        )
        parent_comment.id = "parent-123"
        parent_comment.root_id = "root-123"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=parent_comment)
        mock_db.execute = AsyncMock(return_value=mock_result)

        comment_data = CommentCreate(
            blog_id="blog-123",
            content="Deep reply",
            parent_id="parent-123"
        )

        with pytest.raises(ValueError, match="Maximum reply level exceeded"):
            await service.create_comment(comment_data, author_id="user-123")

    @pytest.mark.asyncio
    async def test_delete_comment(self, service, mock_db):
        comment = Comment(
            blog_id="blog-123",
            author_id="user-123",
            content="Test comment"
        )
        comment.id = "comment-123"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=comment)
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await service.delete_comment("comment-123", "user-123")

        assert result is True
        assert comment.comment_status == 0

    @pytest.mark.asyncio
    async def test_delete_comment_not_found(self, service, mock_db):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await service.delete_comment("nonexistent", "user-123")

        assert result is False

    @pytest.mark.asyncio
    async def test_delete_comment_wrong_author(self, service, mock_db):
        comment = Comment(
            blog_id="blog-123",
            author_id="other-user",
            content="Test comment"
        )
        comment.id = "comment-123"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=comment)
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await service.delete_comment("comment-123", "user-123")

        assert result is False
