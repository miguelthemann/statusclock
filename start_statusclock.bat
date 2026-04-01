@echo off
setlocal
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
    set "PYTHON_EXE=.venv\Scripts\python.exe"
) else (
    set "PYTHON_EXE=python"
)

"%PYTHON_EXE%" -c "import dotenv, PySide6, requests" >nul 2>&1
if errorlevel 1 (
    echo Dependencias em falta.
    echo.
    echo Corre estes comandos na pasta D:\statusclock:
    echo   python -m venv .venv
    echo   .venv\Scripts\Activate.ps1
    echo   pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

"%PYTHON_EXE%" -m src.statusclock
