@echo off
echo ======================================================
echo   Joao - Secretario Escolar - Instalador de Ferramentas (Ambiente)
echo ======================================================
echo.
echo Verificando e instalando bibliotecas necessarias...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
echo.
echo ======================================================
echo   Concluido! Agora voce pode rodar o sistema.
echo ======================================================
pause
