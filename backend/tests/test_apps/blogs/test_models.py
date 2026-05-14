import pytest
from apps.blogs.models import Blog
from apps.comments.models import Comment


class TestBlogModel:
    def test_blog_create(self):
        blog = Blog(
            title="Test Blog",
            content="Test content",
            author_id="test-uuid",
            status="published",
            is_deleted=False,
        )
        assert blog.title == "Test Blog"
        assert blog.status == "published"
        assert blog.is_deleted is False
