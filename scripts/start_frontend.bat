@echo off
REM Start Streamlit Frontend
cd /d %~dp0..
call .venv\Scripts\activate
cd frontend
streamlit run app.py
