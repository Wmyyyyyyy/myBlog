from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
import json

class SecurityMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, db_session_factory=None, redis_client=None):
        super().__init__(app)
        self.db_session_factory = db_session_factory
        self.redis_client = redis_client

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else 'unknown'

        # Check IP ban first
        if self.redis_client:
            is_banned = await self._check_ip_ban(client_ip)
            if is_banned:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="当前访问来源异常，已被限制访问，请联系管理员"
                )

        # Process request
        response = await call_next(request)

        # Log security events for error responses
        if response.status_code >= 400:
            await self._log_security_event(
                client_ip=client_ip,
                endpoint=str(request.url.path),
                method=request.method,
                result=str(response.status_code)
            )

        return response

    async def _check_ip_ban(self, ip: str) -> bool:
        """Check if IP is banned"""
        try:
            from apps.admin.services import IPBanService
            async with self.db_session_factory() as db:
                service = IPBanService(db, self.redis_client)
                return await service.check_ip_ban(ip)
        except:
            return False

    async def _log_security_event(self, client_ip: str, endpoint: str, method: str, result: str):
        """Log security event"""
        try:
            from apps.admin.services import SecurityLogService
            async with self.db_session_factory() as db:
                service = SecurityLogService(db, self.redis_client)
                await service.log_security_event(
                    ip=client_ip,
                    endpoint=endpoint,
                    method=method,
                    result=result
                )
        except:
            pass
