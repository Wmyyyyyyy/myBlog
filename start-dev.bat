@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ============================================
echo 博客系统本地开发环境启动脚本 (Windows)
echo ============================================
echo.

REM 检查 Python 版本
echo [1/5] 检查 Python 版本...
python --version >nul 2>&1
if errorlevel 1 (
    echo   [错误] 未找到 Python，请先安装 Python 3.11+
    exit /b 1
)
for /f "tokens=2" %%v in ('python --version 2^>^&1') do set PYTHON_VERSION=%%v
echo   Python %PYTHON_VERSION%

REM 检查 Node.js 版本
echo [2/5] 检查 Node.js 版本...
node --version >nul 2>&1
if errorlevel 1 (
    echo   [错误] 未找到 Node.js，请先安装 Node.js 20+
    exit /b 1
)
for /f "tokens=2" %%v in ('node --version 2^>^&1') do set NODE_VERSION=%%v
echo   Node.js %NODE_VERSION%

REM 检查 Docker
echo [3/5] 检查 Docker...
docker --version >nul 2>&1
if errorlevel 1 (
    echo   [错误] 未找到 Docker，请先安装 Docker Desktop
    exit /b 1
)
docker compose version >nul 2>&1
if errorlevel 1 (
    echo   [错误] Docker Compose 不可用
    exit /b 1
)
echo   Docker 已就绪

REM 启动数据库服务
echo [4/5] 启动 PostgreSQL 和 Redis...
docker compose up -d postgres redis
if errorlevel 1 (
    echo   [错误] 数据库服务启动失败
    exit /b 1
)
echo   数据库服务已启动

REM 等待数据库就绪
echo   等待数据库启动...
timeout /t 5 /nobreak >nul

REM 启动后端
echo [5/5] 启动后端服务...
start "Backend" cmd /k "cd /d %~dp0backend && .venv\Scripts\python.exe -m uvicorn main:app --reload"

REM 等待后端启动
echo   等待后端启动...
timeout /t 3 /nobreak >nul

REM 启动前端
echo 启动前端服务...
start "Frontend" cmd /k "cd /d %~dp0web-client && npm run dev"

echo.
echo ============================================
echo  开发环境已启动！
echo ============================================
echo.
echo   后端 API:  http://localhost:8000/docs
echo   前端:      http://localhost:5173
echo.
echo   关闭时:
echo   - 关闭 Backend 和 Frontend 窗口
echo   - 运行 docker compose down 停止数据库
echo.
pause
