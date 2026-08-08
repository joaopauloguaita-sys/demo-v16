@echo off
title Joao - Secretario Escolar - Instalador
color 0B
echo.
echo  =====================================================
echo    Joao - Secretario Escolar - Instalacao de Dependencias
echo    Escola Municipal Prof. Luiz Antonio Lorenzette
echo    Sistema por Joao Paulo A. Guaita
echo  =====================================================
echo.

echo  [1/2] Verificando Python instalado...
python --version
if errorlevel 1 (
    echo.
    echo  ERRO: Python nao encontrado!
    echo  Acesse https://python.org/downloads
    echo  IMPORTANTE: marque "Add Python to PATH" na instalacao!
    pause
    exit /b 1
)

echo.
echo  [2/2] Instalando todas as bibliotecas necessarias...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo.
echo  =====================================================
echo    INSTALACAO CONCLUIDA COM SUCESSO!
echo    Para iniciar: clique em iniciar.bat
echo  =====================================================
echo.
pause
