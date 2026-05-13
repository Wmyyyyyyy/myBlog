@echo off
chcp 65001 >nul
echo.
echo 停止数据库服务...
docker compose stop postgres redis
echo.
echo 数据库服务已停止
echo 如需完全清理，运行: docker compose down
pause
