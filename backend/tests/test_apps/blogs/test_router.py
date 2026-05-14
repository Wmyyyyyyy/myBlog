import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


class TestBlogAPI:
    async def test_create_blog_unauthenticated(self, client: AsyncClient):
        """Test that creating a blog without authentication returns 401."""
        response = await client.post("/api/blogs", json={
            "title": "Test",
            "content": "Test content",
        })
        assert response.status_code == 401

    async def test_create_blog(self, client: AsyncClient, faker_email):
        """Test that an authenticated user can create a blog."""
        # Register and login first
        await client.post("/api/auth/register", json={
            "username": "bloguser",
            "email": faker_email,
            "password": "SecurePass123",
        })
        login_resp = await client.post(
            "/api/auth/login",
            data={"username": "bloguser", "password": "SecurePass123"},
        )
        token = login_resp.json()["access_token"]

        response = await client.post(
            "/api/blogs",
            json={"title": "My First Blog", "content": "Hello world"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "My First Blog"
        assert "id" in data

    async def test_list_blogs(self, client: AsyncClient):
        """Test listing blogs returns a list."""
        response = await client.get("/api/blogs")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    async def test_get_blog(self, client: AsyncClient, faker_email):
        """Test getting a single blog by ID."""
        # Create a blog first
        await client.post("/api/auth/register", json={
            "username": "bloguser2",
            "email": faker_email,
            "password": "SecurePass123",
        })
        login_resp = await client.post(
            "/api/auth/login",
            data={"username": "bloguser2", "password": "SecurePass123"},
        )
        token = login_resp.json()["access_token"]

        create_resp = await client.post(
            "/api/blogs",
            json={"title": "Test Blog", "content": "Test content"},
            headers={"Authorization": f"Bearer {token}"},
        )
        blog_id = create_resp.json()["id"]

        # Get the blog
        response = await client.get(f"/api/blogs/{blog_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == blog_id
        assert data["title"] == "Test Blog"

    async def test_get_blog_not_found(self, client: AsyncClient):
        """Test getting a non-existent blog returns 404."""
        response = await client.get("/api/blogs/00000000-0000-0000-0000-000000000001")
        assert response.status_code == 404

    async def test_update_blog(self, client: AsyncClient, faker_email):
        """Test updating a blog."""
        # Create a blog first
        await client.post("/api/auth/register", json={
            "username": "bloguser3",
            "email": faker_email,
            "password": "SecurePass123",
        })
        login_resp = await client.post(
            "/api/auth/login",
            data={"username": "bloguser3", "password": "SecurePass123"},
        )
        token = login_resp.json()["access_token"]

        create_resp = await client.post(
            "/api/blogs",
            json={"title": "Original Title", "content": "Original content"},
            headers={"Authorization": f"Bearer {token}"},
        )
        blog_id = create_resp.json()["id"]

        # Update the blog
        response = await client.put(
            f"/api/blogs/{blog_id}",
            json={"title": "Updated Title"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"

    async def test_delete_blog(self, client: AsyncClient, faker_email):
        """Test deleting a blog."""
        # Create a blog first
        await client.post("/api/auth/register", json={
            "username": "bloguser4",
            "email": faker_email,
            "password": "SecurePass123",
        })
        login_resp = await client.post(
            "/api/auth/login",
            data={"username": "bloguser4", "password": "SecurePass123"},
        )
        token = login_resp.json()["access_token"]

        create_resp = await client.post(
            "/api/blogs",
            json={"title": "To Delete", "content": "Content"},
            headers={"Authorization": f"Bearer {token}"},
        )
        blog_id = create_resp.json()["id"]

        # Delete the blog
        response = await client.delete(
            f"/api/blogs/{blog_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert response.json()["message"] == "Blog deleted successfully"

    async def test_increment_view_count(self, client: AsyncClient, faker_email):
        """Test that viewing a blog increments its view count."""
        # Create a blog first
        await client.post("/api/auth/register", json={
            "username": "bloguser5",
            "email": faker_email,
            "password": "SecurePass123",
        })
        login_resp = await client.post(
            "/api/auth/login",
            data={"username": "bloguser5", "password": "SecurePass123"},
        )
        token = login_resp.json()["access_token"]

        create_resp = await client.post(
            "/api/blogs",
            json={"title": "View Count Test", "content": "Content"},
            headers={"Authorization": f"Bearer {token}"},
        )
        blog_id = create_resp.json()["id"]

        # View the blog twice
        await client.get(f"/api/blogs/{blog_id}")
        await client.get(f"/api/blogs/{blog_id}")

        # Check the view count
        response = await client.get(f"/api/blogs/{blog_id}")
        assert response.status_code == 200
        assert response.json()["view_count"] >= 1