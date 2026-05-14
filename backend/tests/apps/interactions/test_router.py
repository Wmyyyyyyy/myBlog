import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


class TestFavoriteAPI:
    async def test_add_favorite_unauthenticated(self, client: AsyncClient):
        """Test that adding a favorite without authentication returns 401."""
        response = await client.post("/api/interactions/favorites/test-blog-id")
        assert response.status_code == 401

    async def test_remove_favorite_unauthenticated(self, client: AsyncClient):
        """Test that removing a favorite without authentication returns 401."""
        response = await client.delete("/api/interactions/favorites/test-blog-id")
        assert response.status_code == 401

    async def test_get_favorites_status_unauthenticated(self, client: AsyncClient):
        """Test that checking favorite status without authentication returns 401."""
        response = await client.get("/api/interactions/favorites/test-blog-id/status")
        assert response.status_code == 401

    async def test_get_my_favorites_unauthenticated(self, client: AsyncClient):
        """Test that getting my favorites without authentication returns 401."""
        response = await client.get("/api/interactions/favorites")
        assert response.status_code == 401


class TestLikeAPI:
    async def test_add_like_unauthenticated(self, client: AsyncClient):
        """Test that adding a like without authentication returns 401."""
        response = await client.post("/api/interactions/likes/test-blog-id")
        assert response.status_code == 401

    async def test_remove_like_unauthenticated(self, client: AsyncClient):
        """Test that removing a like without authentication returns 401."""
        response = await client.delete("/api/interactions/likes/test-blog-id")
        assert response.status_code == 401

    async def test_get_likes_status_unauthenticated(self, client: AsyncClient):
        """Test that checking like status without authentication returns 401."""
        response = await client.get("/api/interactions/likes/test-blog-id/status")
        assert response.status_code == 401


class TestFollowAPI:
    async def test_follow_user_unauthenticated(self, client: AsyncClient):
        """Test that following a user without authentication returns 401."""
        response = await client.post("/api/interactions/follows/test-user-id")
        assert response.status_code == 401

    async def test_unfollow_user_unauthenticated(self, client: AsyncClient):
        """Test that unfollowing a user without authentication returns 401."""
        response = await client.delete("/api/interactions/follows/test-user-id")
        assert response.status_code == 401

    async def test_get_follow_status_unauthenticated(self, client: AsyncClient):
        """Test that checking follow status without authentication returns 401."""
        response = await client.get("/api/interactions/follows/test-user-id/status")
        assert response.status_code == 401

    async def test_get_followers_unauthenticated(self, client: AsyncClient):
        """Test that getting followers for a non-existent user returns empty list."""
        response = await client.get("/api/interactions/followers/00000000-0000-0000-0000-000000000004")
        assert response.status_code == 200
        assert response.json() == []

    async def test_get_following_unauthenticated(self, client: AsyncClient):
        """Test that getting following for a non-existent user returns empty list."""
        response = await client.get("/api/interactions/following/00000000-0000-0000-0000-000000000005")
        assert response.status_code == 200
        assert response.json() == []
