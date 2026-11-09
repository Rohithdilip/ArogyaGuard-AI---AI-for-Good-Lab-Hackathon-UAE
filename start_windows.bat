@echo off
cd /d "%~dp0"
if not exist .venv (py -m venv .venv)
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 (pause & exit /b 1)
.venv\Scripts\python.exe run.py
pause
