from celery import Celery
from celery.schedules import crontab
from core.config import settings

celery_app = Celery('daily_reset', broker=settings.REDIS_URL)
celery_app.config_from_object('tasks.celery_config')

celery_app.conf.beat_schedule = {
    'reset-missed-checkins': {
        'task': 'tasks.daily_reset.reset_missed_checkins',
        'schedule': crontab(hour=4, minute=0),  # 04:00 UTC = 00:00 Beijing
    },
}


@celery_app.task
def reset_missed_checkins():
    """每天 04:00 UTC 检查昨天漏打卡的用户，重置连续天数"""
    from core.database import AsyncSessionLocal
    from apps.foundation.services import FoundationService
    import asyncio

    async def _do_reset():
        async with AsyncSessionLocal() as session:
            service = FoundationService(session)
            count = await service.reset_missed_checkins()
            return count

    return asyncio.run(_do_reset())
