from celery.schedules import crontab

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
}
