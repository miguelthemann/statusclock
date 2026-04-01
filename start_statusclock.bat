@echo off
setlocal
cd /d "%~dp0"

set "PROJECT_DIR=%CD%"

if exist ".venv\Scripts\python.exe" (
    set "PYTHON_EXE=.venv\Scripts\python.exe"
) else (
    set "PYTHON_EXE=python"
)

"%PYTHON_EXE%" -c "import dotenv, PySide6, requests" >nul 2>&1
if errorlevel 1 (
    echo Dependencias em falta.
    echo.
    echo Corre primeiro o setup nesta pasta:
    echo   "%PROJECT_DIR%\setup_statusclock.bat"
    echo.
    pause
    exit /b 1
)

"%PYTHON_EXE%" -m src.statusclock

