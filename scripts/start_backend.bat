@echo off
REM Start Flask Backend
cd /d %~dp0..
call .venv\Scripts\activate
cd backend
python app.py
