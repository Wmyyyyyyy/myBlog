@echo off
cd /d %~dp0
echo Activating virtual environment...
call .venv\Scripts\activate
echo Starting backend server...
uvicorn main:app --reload --host 0.0.0.0 --port 8000
pause
