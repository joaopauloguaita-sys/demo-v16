@echo off
cd /d "%~dp0"
python main.py
if errorlevel 1 (
    echo.
    echo ERRO ao iniciar. Verifique se rodou instalar.bat primeiro.
    pause
)
