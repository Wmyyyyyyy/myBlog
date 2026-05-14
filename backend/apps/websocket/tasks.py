import asyncio
from apps.websocket.manager import manager

PURGE_INTERVAL = 30  # 秒
PURGE_TIMEOUT = 60   # 超时秒数


async def _purge_loop():
    """定期清理超时连接的后台任务"""
    while True:
        try:
            await asyncio.sleep(PURGE_INTERVAL)
            await manager.purge_inactive(timeout=PURGE_TIMEOUT)
        except asyncio.CancelledError:
            break
        except Exception:
            # 记录错误但不中断循环
            import logging
            logging.warning(f"Error in purge loop: {e}")


_purge_task: asyncio.Task = None


def start_purge_task():
    global _purge_task
    _purge_task = asyncio.create_task(_purge_loop())


def stop_purge_task():
    global _purge_task
    if _purge_task:
        _purge_task.cancel()
        _purge_task = None