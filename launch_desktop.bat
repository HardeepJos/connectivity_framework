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
echo Starting Connectivity Desktop App...
%PYTHON% -m wearables.tk_ui
if errorlevel 1 (
    echo.
    echo Could not start the desktop app. Check Python and Tkinter installation.
    pause
)
