@echo off
cd /d "%~dp0"
"%~dp0.venv\Scripts\python.exe" -X utf8 "%~dp0run.py" --backend mysql
pause
