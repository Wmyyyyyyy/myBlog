import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from apps.websocket.manager import ConnectionManager


class TestConnectionManager:
    """Test ConnectionManager multi-device support"""

    @pytest.fixture
    def manager(self):
        return ConnectionManager()

    @pytest.fixture
    def mock_websocket(self):
        ws = MagicMock()
        ws.accept = AsyncMock()
        ws.send_json = AsyncMock()
        ws.close = AsyncMock()
        return ws

    @pytest.mark.asyncio
    async def test_connect_single_device(self, manager, mock_websocket):
        """Test connecting a single device"""
        with patch.object(manager, "_get_redis") as mock_get_redis:
            mock_redis = AsyncMock()
            mock_get_redis.return_value = mock_redis

            await manager.connect(mock_websocket, user_id=1)

            assert 1 in manager.connections
            assert mock_websocket in manager.connections[1]
            assert mock_websocket in manager.last_heartbeat
            mock_redis.setex.assert_called_once_with("ws:online:1", 60, "1")

    @pytest.mark.asyncio
    async def test_connect_multiple_devices_same_user(self, manager, mock_websocket):
        """Test that same user can have multiple WebSocket connections (multi-device)"""
        ws1 = mock_websocket
        ws2 = MagicMock()
        ws2.accept = AsyncMock()
        ws2.send_json = AsyncMock()

        with patch.object(manager, "_get_redis") as mock_get_redis:
            mock_redis = AsyncMock()
            mock_get_redis.return_value = mock_redis

            await manager.connect(ws1, user_id=1)
            await manager.connect(ws2, user_id=1)

            assert 1 in manager.connections
            assert len(manager.connections[1]) == 2
            assert ws1 in manager.connections[1]
            assert ws2 in manager.connections[1]

    @pytest.mark.asyncio
    async def test_disconnect_one_device_preserves_another(self, manager, mock_websocket):
        """Test disconnecting one device does not affect other connections"""
        ws1 = mock_websocket
        ws2 = MagicMock()
        ws2.accept = AsyncMock()
        ws2.send_json = AsyncMock()

        with patch.object(manager, "_get_redis") as mock_get_redis:
            mock_redis = AsyncMock()
            mock_get_redis.return_value = mock_redis

            await manager.connect(ws1, user_id=1)
            await manager.connect(ws2, user_id=1)
            await manager.disconnect(ws1, user_id=1)

            assert 1 in manager.connections
            assert len(manager.connections[1]) == 1
            assert ws2 in manager.connections[1]
            assert ws1 not in manager.connections[1]
            mock_redis.delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_last_device_disconnect_removes_redis_key(self, manager, mock_websocket):
        """Test that when last connection disconnects, Redis key is removed"""
        with patch.object(manager, "_get_redis") as mock_get_redis:
            mock_redis = AsyncMock()
            mock_get_redis.return_value = mock_redis

            await manager.connect(mock_websocket, user_id=1)
            await manager.disconnect(mock_websocket, user_id=1)

            assert 1 not in manager.connections
            mock_redis.delete.assert_called_once_with("ws:online:1")

    @pytest.mark.asyncio
    async def test_heartbeat_refreshes_ttl(self, manager, mock_websocket):
        """Test heartbeat updates last_heartbeat and refreshes Redis TTL"""
        with patch.object(manager, "_get_redis") as mock_get_redis:
            mock_redis = AsyncMock()
            mock_get_redis.return_value = mock_redis

            await manager.connect(mock_websocket, user_id=1)
            original_time = manager.last_heartbeat[mock_websocket]

            await asyncio.sleep(0.01)
            await manager.heartbeat(mock_websocket, user_id=1)

            assert manager.last_heartbeat[mock_websocket] >= original_time
            mock_redis.setex.assert_called()

    @pytest.mark.asyncio
    async def test_broadcast_to_users(self, manager, mock_websocket):
        """Test broadcasting message to multiple users"""
        ws1 = mock_websocket
        ws2 = MagicMock()
        ws2.accept = AsyncMock()
        ws2.send_json = AsyncMock()

        with patch.object(manager, "_get_redis") as mock_get_redis:
            mock_redis = AsyncMock()
            mock_get_redis.return_value = mock_redis

            await manager.connect(ws1, user_id=1)
            await manager.connect(ws2, user_id=2)

            message = {"type": "test", "data": "hello"}
            await manager.broadcast_to_users([1, 2], message)

            ws1.send_json.assert_called_once_with(message)
            ws2.send_json.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_broadcast_removes_dead_connections(self, manager, mock_websocket):
        """Test that dead connections are removed during broadcast"""
        ws1 = mock_websocket
        ws1.send_json.side_effect = Exception("Connection closed")

        with patch.object(manager, "_get_redis") as mock_get_redis:
            mock_redis = AsyncMock()
            mock_get_redis.return_value = mock_redis

            await manager.connect(ws1, user_id=1)
            message = {"type": "test", "data": "hello"}
            await manager.broadcast_to_users([1], message)

            assert 1 not in manager.connections

    @pytest.mark.asyncio
    async def test_purge_inactive(self, manager, mock_websocket):
        """Test that inactive connections are purged"""
        with patch.object(manager, "_get_redis") as mock_get_redis:
            mock_redis = AsyncMock()
            mock_get_redis.return_value = mock_redis

            await manager.connect(mock_websocket, user_id=1)
            manager.last_heartbeat[mock_websocket] = time.time() - 120

            await manager.purge_inactive(timeout=60)

            assert 1 not in manager.connections
            mock_redis.delete.assert_called()

    @pytest.mark.asyncio
    async def test_get_online_count(self, manager):
        """Test counting online users via Redis SCAN"""
        with patch.object(manager, "_get_redis") as mock_get_redis:
            mock_redis = AsyncMock()
            mock_get_redis.return_value = mock_redis
            mock_redis.scan = AsyncMock(side_effect=[
                (100, [b"ws:online:1", b"ws:online:2"]),
                (0, [b"ws:online:3"])
            ])

            count = await manager.get_online_count()

            assert count == 3
            assert mock_redis.scan.call_count == 2

    @pytest.mark.asyncio
    async def test_disconnect_non_existent_user(self, manager, mock_websocket):
        """Test disconnecting a user that doesn't exist doesn't raise errors"""
        with patch.object(manager, "_get_redis") as mock_get_redis:
            mock_redis = AsyncMock()
            mock_get_redis.return_value = mock_redis

            await manager.disconnect(mock_websocket, user_id=999)
            assert 999 not in manager.connections
