@echo off
REM Start Development Environment
REM Starts both the Flask backend and the Streamlit frontend in separate windows.

echo Starting RamGAP development environment...

start "RamGAP Backend" cmd /k "cd /d %~dp0..\.. && .venv\Scripts\activate && cd RamGAP\backend && python app.py"
timeout /t 2 >nul
start "RamGAP Frontend" cmd /k "cd /d %~dp0..\.. && .venv\Scripts\activate && cd RamGAP\frontend && streamlit run app.py"

echo Backend:  http://localhost:5050
echo Frontend: http://localhost:8501
