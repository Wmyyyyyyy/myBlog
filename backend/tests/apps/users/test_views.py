import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

async def test_register(client: AsyncClient):
    response = await client.post(
        "/api/auth/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpassword123",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"
    assert "id" in data

async def test_register_duplicate_username(client: AsyncClient):
    await client.post(
        "/api/auth/register",
        json={
            "username": "duplicateuser",
            "email": "first@example.com",
            "password": "testpassword123",
        },
    )

    response = await client.post(
        "/api/auth/register",
        json={
            "username": "duplicateuser",
            "email": "second@example.com",
            "password": "testpassword123",
        },
    )
    assert response.status_code == 400

async def test_login(client: AsyncClient):
    await client.post(
        "/api/auth/register",
        json={
            "username": "logintest",
            "email": "login@example.com",
            "password": "testpassword123",
        },
    )

    response = await client.post(
        "/api/auth/login",
        data={
            "username": "logintest",
            "password": "testpassword123",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"

async def test_login_invalid_credentials(client: AsyncClient):
    response = await client.post(
        "/api/auth/login",
        data={
            "username": "nonexistent",
            "password": "wrongpassword",
        },
    )
    assert response.status_code == 401

async def test_get_me(client: AsyncClient):
    register_response = await client.post(
        "/api/auth/register",
        json={
            "username": "meuser",
            "email": "me@example.com",
            "password": "testpassword123",
        },
    )
    user_id = register_response.json()["id"]

    login_response = await client.post(
        "/api/auth/login",
        data={
            "username": "meuser",
            "password": "testpassword123",
        },
    )
    access_token = login_response.json()["access_token"]

    response = await client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == user_id
    assert data["username"] == "meuser"

async def test_get_me_unauthorized(client: AsyncClient):
    response = await client.get("/api/auth/me")
    assert response.status_code == 401

async def test_refresh_token(client: AsyncClient):
    await client.post(
        "/api/auth/register",
        json={
            "username": "refreshuser",
            "email": "refresh@example.com",
            "password": "testpassword123",
        },
    )

    login_response = await client.post(
        "/api/auth/login",
        data={
            "username": "refreshuser",
            "password": "testpassword123",
        },
    )
    refresh_token = login_response.json()["refresh_token"]

    response = await client.post(
        "/api/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data

async def test_logout(client: AsyncClient):
    await client.post(
        "/api/auth/register",
        json={
            "username": "logoutuser",
            "email": "logout@example.com",
            "password": "testpassword123",
        },
    )

    login_response = await client.post(
        "/api/auth/login",
        data={
            "username": "logoutuser",
            "password": "testpassword123",
        },
    )
    access_token = login_response.json()["access_token"]

    response = await client.post(
        "/api/auth/logout",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Successfully logged out"
