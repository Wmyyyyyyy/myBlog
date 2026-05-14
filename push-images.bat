@echo off
echo ================================
echo Push base images to private registry
echo ================================

echo.
echo [1/3] Push Python image...
docker pull python:3.11-slim
docker tag python:3.11-slim ccr.ccs.tencentyun.com/blog_b/python:3.11-slim
docker push ccr.ccs.tencentyun.com/blog_b/python:3.11-slim

echo.
echo [2/3] Push PostgreSQL image...
docker pull postgres:15
docker tag postgres:15 ccr.ccs.tencentyun.com/blog_b/postgres:15
docker push ccr.ccs.tencentyun.com/blog_b/postgres:15

echo.
echo [3/3] Push Redis image...
docker pull redis:7
docker tag redis:7 ccr.ccs.tencentyun.com/blog_b/redis:7
docker push ccr.ccs.tencentyun.com/blog_b/redis:7

echo.
echo ================================
echo Done!
echo ================================
pause
