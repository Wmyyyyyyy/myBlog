import json
import asyncio
import logging
from typing import Optional
import redis.asyncio as redis
from core.config import settings
from apps.websocket.manager import manager

logger = logging.getLogger(__name__)

CHANNEL = "dynamic_events"


class PubSubConsumer:
    def __init__(self):
        self._redis: Optional[redis.Redis] = None
        self._pubsub: Optional[redis.client.PubSub] = None
        self._task: Optional[asyncio.Task] = None

    async def _get_redis(self) -> redis.Redis:
        if self._redis is None:
            self._redis = redis.from_url(settings.REDIS_URL)
        return self._redis

    async def start(self):
        """启动消费者"""
        self._task = asyncio.create_task(self._consume())

    async def stop(self):
        """停止消费者"""
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        if self._pubsub:
            try:
                await self._pubsub.unsubscribe(CHANNEL)
                await self._pubsub.close()
            except Exception as e:
                logger.warning(f"Error during shutdown: {e}")
        if self._redis:
            await self._redis.close()
            self._redis = None

    async def _consume(self):
        """消费 Redis 消息"""
        r = await self._get_redis()
        self._pubsub = r.pubsub()
        await self._pubsub.subscribe(CHANNEL)

        try:
            async for message in self._pubsub.listen():
                if message["type"] == "message":
                    await self._handle_message(message["data"])
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.warning(f"Error in pubsub listen: {e}")
        finally:
            if self._pubsub:
                try:
                    await self._pubsub.unsubscribe(CHANNEL)
                    await self._pubsub.close()
                except Exception as e:
                    logger.warning(f"Error during shutdown: {e}")

    async def _handle_message(self, data: bytes):
        """处理动态事件消息"""
        try:
            msg = json.loads(data.decode())
        except Exception as e:
            logger.warning(f"Failed to process message: {e}")
            return

        if msg.get("type") != "dynamic":
            return

        event_type = msg.get("event_type")
        user_id = msg.get("user_id")
        target_user_ids = msg.get("target_user_ids", [])

        if not target_user_ids:
            return

        # 推送消息给目标用户
        push_message = {
            "type": "dynamic",
            "event_type": event_type,
            "user_id": user_id,
            "target_id": msg.get("target_id"),
            "data": msg.get("data", {})
        }

        await manager.broadcast_to_users(target_user_ids, push_message)


# 全局单例
consumer = PubSubConsumer()