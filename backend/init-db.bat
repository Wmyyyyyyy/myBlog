@echo off
cd /d %~dp0
call .venv\Scripts\activate
python init_db.py
pause
