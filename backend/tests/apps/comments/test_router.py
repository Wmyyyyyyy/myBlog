import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


class TestCommentAPI:
    async def test_create_comment_unauthenticated(self, client: AsyncClient):
        """Test that creating a comment without authentication returns 401."""
        response = await client.post("/api/comments", json={
            "blog_id": "some-blog-id",
            "content": "Test comment",
        })
        assert response.status_code == 401

    async def test_get_blog_comments_empty(self, client: AsyncClient):
        """Test getting comments for a blog with no comments."""
        response = await client.get("/api/comments/blog/nonexistent-blog")
        assert response.status_code == 200
        assert response.json() == []

    async def test_get_blog_comments_with_pagination(self, client: AsyncClient):
        """Test getting blog comments with pagination parameters."""
        response = await client.get(
            "/api/comments/blog/test-blog?skip=0&limit=10&sort=latest"
        )
        assert response.status_code == 200

    async def test_get_blog_comments_invalid_sort(self, client: AsyncClient):
        """Test that invalid sort parameter returns 422."""
        response = await client.get("/api/comments/blog/test-blog?sort=invalid")
        assert response.status_code == 422

    async def test_get_replies_pagination(self, client: AsyncClient):
        """Test getting comment replies with pagination."""
        response = await client.get(
            "/api/comments/some-comment-id/replies?skip=0&limit=10"
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)
