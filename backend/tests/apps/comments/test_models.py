import pytest
from apps.comments.models import Comment


class TestCommentModel:
    def test_comment_create(self):
        comment = Comment(
            blog_id="blog-uuid",
            author_id="user-uuid",
            content="Test comment",
            level=0,
        )
        assert comment.level == 0
        assert comment.comment_status == 1
        assert comment.like_count == 0

    def test_soft_delete(self):
        comment = Comment(
            blog_id="blog-uuid",
            author_id="user-uuid",
            content="Test comment",
        )
        comment.comment_status = 0
        assert comment.is_deleted is True
