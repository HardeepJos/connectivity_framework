@echo off
setlocal
cd /d "%~dp0"
set "PYTHONPATH=%CD%\src"
where py >nul 2>&1
if %errorlevel%==0 (
    set "PYTHON=py"
) else (
    set "PYTHON=python"
)
echo Starting Meta Wearables UI...
echo Open http://127.0.0.1:8765 in your browser.
%PYTHON% -m wearables.web --host 127.0.0.1 --port 8765
if errorlevel 1 (
    echo.
    echo Could not start the UI. Install Python 3.10 or newer and try again.
    pause
)