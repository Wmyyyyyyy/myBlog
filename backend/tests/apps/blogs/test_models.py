import pytest
from apps.blogs.models import Blog, Comment


class TestBlogModel:
    def test_blog_create(self):
        blog = Blog(
            title="Test Blog",
            content="Test content",
            author_id="test-uuid",
        )
        assert blog.title == "Test Blog"
        assert blog.status == "published"
        assert blog.is_deleted is False
