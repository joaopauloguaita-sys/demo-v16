@echo off
title Joao - Secretario Escolar - Gerando Instalador EXE
color 0B
echo.
echo  =====================================================
echo    Joao - Secretario Escolar - Gerador de Instalador Profissional
echo    Escola Municipal Prof. Luiz Antonio Lorenzette
echo    Sistema por Joao Paulo A. Guaita
echo  =====================================================
echo.
echo  Este processo vai gerar os 3 executaveis do sistema:
echo    1. JoaoOSecretario.exe (programa principal)
echo    2. Inspetores.exe    (painel de saida dos alunos)
echo    3. GestaoPainel.exe  (painel de gestao geral)
echo.
echo  Pode levar de 5 a 15 minutos. Aguarde...
echo.

REM Verificar Python
python --version >nul 2>&1
if errorlevel 1 (
    echo  ERRO: Python nao encontrado!
    echo  Instale o Python em python.org/downloads
    pause
    exit /b 1
)

REM Instalar todas as dependencias (inclui pyinstaller)
echo  [1/4] Instalando/atualizando todas as dependencias...
python -m pip install -r requirements.txt --upgrade

REM Gerar o EXE principal
REM Usamos "python -m PyInstaller" em vez de "pyinstaller" direto porque em
REM muitos PCs a pasta Scripts do Python nao esta no PATH do Windows, e ai
REM o comando "pyinstaller" sozinho nao e reconhecido.
echo.
echo  [2/4] Gerando o programa principal (JoaoOSecretario.exe)...
python -m PyInstaller EscolaGest.spec --clean --noconfirm
if errorlevel 1 (
    echo  ERRO ao gerar o JoaoOSecretario.exe. Veja as mensagens acima.
    pause
    exit /b 1
)

REM Gerar o painel Inspetores
echo.
echo  [3/4] Gerando o painel Inspetores.exe...
python -m PyInstaller Inspetores.spec --clean --noconfirm
if errorlevel 1 (
    echo  ERRO ao gerar o Inspetores.exe. Veja as mensagens acima.
    pause
    exit /b 1
)

REM Gerar o Painel de Gestao
echo.
echo  [4/4] Gerando o GestaoPainel.exe...
python -m PyInstaller GestaoPainel.spec --clean --noconfirm
if errorlevel 1 (
    echo  ERRO ao gerar o GestaoPainel.exe. Veja as mensagens acima.
    pause
    exit /b 1
)

echo.
echo  =====================================================
echo    SUCESSO! Executaveis gerados em:
echo    dist\JoaoOSecretario\JoaoOSecretario.exe
echo    dist\Inspetores\Inspetores.exe
echo    dist\GestaoPainel\GestaoPainel.exe
echo  =====================================================
echo.
echo  Proximo passo: abra o EscolaGest_Installer.nsi com o
echo  programa NSIS para gerar o instalador unico (.exe).
echo.
pause
