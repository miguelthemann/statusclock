@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    python -m venv .venv
)

call ".venv\Scripts\activate.bat"
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

if not exist ".env" if exist ".env.example" (
    copy /y ".env.example" ".env" >nul
)

echo.
echo Setup concluido.
echo.
echo Para arrancar a app:
echo   D:\statusclock\start_statusclock.bat
