import time
from typing import Dict, List
from fastapi import WebSocket
import redis.asyncio as redis
from core.config import settings


class ConnectionManager:
    def __init__(self):
        self.connections: Dict[int, List[WebSocket]] = {}
        self.last_heartbeat: Dict[WebSocket, float] = {}
        self._redis = None

    async def _get_redis(self) -> redis.Redis:
        if self._redis is None:
            self._redis = redis.from_url(settings.REDIS_URL)
        return self._redis

    async def connect(self, ws: WebSocket, user_id: int):
        await ws.accept()
        self.connections.setdefault(user_id, []).append(ws)
        self.last_heartbeat[ws] = time.time()
        r = await self._get_redis()
        await r.setex(f"ws:online:{user_id}", 60, "1")

    async def disconnect(self, ws: WebSocket, user_id: int):
        if user_id in self.connections:
            if ws in self.connections[user_id]:
                self.connections[user_id].remove(ws)
            if not self.connections[user_id]:
                del self.connections[user_id]
                r = await self._get_redis()
                await r.delete(f"ws:online:{user_id}")
        self.last_heartbeat.pop(ws, None)

    async def heartbeat(self, ws: WebSocket, user_id: int):
        self.last_heartbeat[ws] = time.time()
        r = await self._get_redis()
        await r.setex(f"ws:online:{user_id}", 60, "1")

    async def broadcast_to_users(self, user_ids: List[int], message: dict):
        for user_id in user_ids:
            if user_id in self.connections:
                dead_ws = []
                for ws in self.connections[user_id]:
                    try:
                        await ws.send_json(message)
                    except Exception:
                        dead_ws.append(ws)
                for ws in dead_ws:
                    await self.disconnect(ws, user_id)

    async def purge_inactive(self, timeout: float = 60.0):
        now = time.time()
        dead = []
        for ws, last_time in list(self.last_heartbeat.items()):
            if now - last_time > timeout:
                dead.append(ws)
        for ws in dead:
            for uid, ws_list in list(self.connections.items()):
                if ws in ws_list:
                    await self.disconnect(ws, uid)
                    break

    async def get_online_count(self) -> int:
        r = await self._get_redis()
        count = 0
        cursor = 0
        while True:
            cursor, keys = await r.scan(cursor=cursor, match="ws:online:*", count=100)
            count += len(keys)
            if cursor == 0:
                break
        return count


manager = ConnectionManager()
