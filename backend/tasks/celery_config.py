from celery import Celery
from celery.schedules import crontab
from core.config import settings

celery_app = Celery('celery_config', broker=settings.REDIS_URL)

broker_url = 'redis://localhost:6379/0'
result_backend = 'redis://localhost:6379/0'

task_serializer = 'json'
accept_content = ['json']
result_serializer = 'json'
timezone = 'UTC'
enable_utc = True

beat_schedule = {
    'reset-missed-checkins': {
        'task': 'tasks.daily_reset.reset_missed_checkins',
        'schedule': crontab(hour=4, minute=0),  # 04:00 UTC = 00:00 Beijing
    },
    'cleanup-expired-ip-bans': {
        'task': 'tasks.celery_config.cleanup_expired_ip_bans',
        'schedule': crontab(hour=0, minute=0),  # Daily at midnight
    },
}


@celery_app.task
def cleanup_expired_ip_bans():
    """清理过期的 IP 封禁"""
    from core.database import async_session_maker
    from apps.admin.services import IPBanService
    import asyncio

    async def _do_cleanup():
        async with async_session_maker() as session:
            service = IPBanService(session, None)  # No redis needed for cleanup
            count = await service.cleanup_expired_bans()
            return count

    return asyncio.run(_do_cleanup())
