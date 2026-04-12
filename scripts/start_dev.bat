@echo off
REM Start Development Environment
REM Starts both the Flask backend and the Streamlit frontend in separate windows.

echo Starting RamGAP development environment...

REM Kill any existing process on port 5050 before starting
for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr ":5050" ^| findstr "LISTENING"') do (
    echo Killing existing backend on port 5050 PID %%a...
    taskkill /PID %%a /F >nul 2>&1
)

start "RamGAP Backend" cmd /k "cd /d %~dp0..\.. && .venv\Scripts\activate && cd RamGAP\backend && python app.py"
timeout /t 2 >nul
start "RamGAP Frontend" cmd /k "cd /d %~dp0..\.. && .venv\Scripts\activate && cd RamGAP\frontend && streamlit run app.py"

echo Backend:  http://localhost:5050
echo Frontend: http://localhost:8501
