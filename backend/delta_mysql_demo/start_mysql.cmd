@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Python environment is missing. Follow README.txt first.
  pause
  exit /b 2
)
".venv\Scripts\python.exe" continue_mysql.py
if errorlevel 1 (
  echo.
  echo MySQL step did not finish. Read the error above. No existing database was changed.
) else (
  echo.
  echo PASS: Delta and MySQL values match. See runs\...\mysql_validation.json.
)
pause
