import asyncio
import logging
import time
from typing import Dict, List
from fastapi import WebSocket
import redis.asyncio as redis
from core.config import settings


class ConnectionManager:
    def __init__(self):
        self.connections: Dict[int, List[WebSocket]] = {}
        self.last_heartbeat: Dict[WebSocket, float] = {}
        self._lock = asyncio.Lock()
        self._redis = None

    async def _get_redis(self) -> redis.Redis:
        if self._redis is None:
            self._redis = redis.from_url(settings.REDIS_URL)
        return self._redis

    async def connect(self, ws: WebSocket, user_id: int):
        await ws.accept()
        async with self._lock:
            self.connections.setdefault(user_id, []).append(ws)
            self.last_heartbeat[ws] = time.time()
        try:
            r = await self._get_redis()
            await r.setex(f"ws:online:{user_id}", 60, "1")
        except Exception as e:
            logging.warning(f"Redis connect failed: {e}")

    async def disconnect(self, ws: WebSocket, user_id: int):
        async with self._lock:
            if user_id in self.connections:
                if ws in self.connections[user_id]:
                    self.connections[user_id].remove(ws)
                if not self.connections[user_id]:
                    del self.connections[user_id]
                    try:
                        r = await self._get_redis()
                        await r.delete(f"ws:online:{user_id}")
                    except Exception as e:
                        logging.warning(f"Redis disconnect failed: {e}")
            self.last_heartbeat.pop(ws, None)

    async def heartbeat(self, ws: WebSocket, user_id: int):
        async with self._lock:
            self.last_heartbeat[ws] = time.time()
        try:
            r = await self._get_redis()
            await r.setex(f"ws:online:{user_id}", 60, "1")
        except Exception as e:
            logging.warning(f"Redis heartbeat failed: {e}")

    async def broadcast_to_users(self, user_ids: List[int], message: dict):
        for user_id in user_ids:
            async with self._lock:
                ws_list = list(self.connections.get(user_id, []))
            dead_ws = []
            for ws in ws_list:
                try:
                    await ws.send_json(message)
                except Exception:
                    dead_ws.append(ws)
            for ws in dead_ws:
                await self.disconnect(ws, user_id)

    async def purge_inactive(self, timeout: float = 60.0):
        now = time.time()
        dead = []  # list of (ws, user_id)
        async with self._lock:
            for ws, last_time in list(self.last_heartbeat.items()):
                if now - last_time > timeout:
                    for uid, ws_list in list(self.connections.items()):
                        if ws in ws_list:
                            dead.append((ws, uid))
                            break
        for ws, uid in dead:
            await self.disconnect(ws, uid)

    async def get_online_count(self) -> int:
        try:
            r = await self._get_redis()
            count = 0
            cursor = 0
            while True:
                cursor, keys = await r.scan(cursor=cursor, match="ws:online:*", count=100)
                count += len(keys)
                if cursor == 0:
                    break
            return count
        except Exception as e:
            logging.warning(f"Redis get_online_count failed: {e}")
            return 0

    async def close(self):
        if self._redis:
            await self._redis.close()
            self._redis = None


manager = ConnectionManager()
