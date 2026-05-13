import redis.asyncio as redis
from core.config import settings

redis_client = redis.from_url(
    settings.REDIS_URL,
    encoding="utf-8",
    decode_responses=True,
)

async def close_redis():
    await redis_client.close()
