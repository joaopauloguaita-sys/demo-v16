; EscolaGest_Installer.nsi
; Instalador profissional gerado com NSIS
; Para compilar: instale o NSIS (nsis.sourceforge.io) e abra este arquivo

!define APP_NAME      "João - Secretário Escolar"
!define APP_VERSION   "3.2"
!define APP_PUBLISHER "João Paulo A. Guaita"
!define APP_URL       "https://github.com/SEU-USUARIO/escolagest"
!define APP_EXE       "JoaoOSecretario.exe"
!define INSTALL_DIR   "$PROGRAMFILES64\JoaoOSecretario"
!define ESCOLA        "Escola Municipal Professor Luiz Antônio Lorenzette"

; Configurações gerais
Name         "${APP_NAME} ${APP_VERSION}"
OutFile      "JoaoOSecretario_Instalador_v${APP_VERSION}.exe"
InstallDir   "${INSTALL_DIR}"
InstallDirRegKey HKLM "Software\${APP_NAME}" "Install_Dir"
RequestExecutionLevel admin
BrandingText "${ESCOLA} | Sistema por ${APP_PUBLISHER}"

; Ícone do instalador
Icon "assets\escolagest.ico"
UninstallIcon "assets\escolagest.ico"

; Interface moderna
!include "MUI2.nsh"
!define MUI_ICON   "assets\escolagest.ico"
!define MUI_UNICON "assets\escolagest.ico"

; Cores da escola
!define MUI_BGCOLOR         "0b3d4c"
!define MUI_TEXTCOLOR       "f5f7f5"

; Páginas do instalador
!define MUI_WELCOMEPAGE_TITLE  "Bem-vindo ao João - Secretário Escolar ${APP_VERSION}"
!define MUI_WELCOMEPAGE_TEXT   "Este assistente irá instalar o João - Secretário Escolar no seu computador.$\r$\n$\r$\n${ESCOLA}$\r$\nSistema desenvolvido por ${APP_PUBLISHER}$\r$\nLicença cedida gratuitamente.$\r$\n$\r$\nClique em Avançar para continuar."
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!define MUI_FINISHPAGE_RUN         "$INSTDIR\${APP_EXE}"
!define MUI_FINISHPAGE_RUN_TEXT    "Abrir João - Secretário Escolar agora"
!define MUI_FINISHPAGE_SHOWREADME  ""
!insertmacro MUI_PAGE_FINISH

; Páginas de desinstalação
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

; Idioma
!insertmacro MUI_LANGUAGE "PortugueseBR"

; ─── Seção principal de instalação ───────────────────────────────────────────
Section "João - Secretário Escolar (obrigatório)" SecMain
    SectionIn RO
    SetOutPath "$INSTDIR"

    ; Copiar todos os arquivos do dist\JoaoOSecretario\
    File /r "dist\JoaoOSecretario\*.*"

    ; Copiar o painel Inspetores para uma subpasta própria
    SetOutPath "$INSTDIR\Inspetores"
    File /r "dist\Inspetores\*.*"

    ; Copiar o Painel de Gestão para uma subpasta própria
    SetOutPath "$INSTDIR\GestaoPainel"
    File /r "dist\GestaoPainel\*.*"

    SetOutPath "$INSTDIR"

    ; Criar pasta de dados do banco (se não existir)
    CreateDirectory "$INSTDIR\database"

    ; Registrar no Windows (para aparecer em Adicionar/Remover Programas)
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" \
                     "DisplayName"     "${APP_NAME} - ${ESCOLA}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" \
                     "UninstallString" '"$INSTDIR\Uninstall.exe"'
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" \
                     "DisplayIcon"     "$INSTDIR\${APP_EXE}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" \
                     "Publisher"       "${APP_PUBLISHER}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" \
                     "DisplayVersion"  "${APP_VERSION}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" \
                     "URLInfoAbout"    "${APP_URL}"
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" \
                       "NoModify" 1
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" \
                       "NoRepair"  1

    ; Criar desinstalador
    WriteUninstaller "$INSTDIR\Uninstall.exe"

    ; Atalho no Menu Iniciar
    CreateDirectory "$SMPROGRAMS\${APP_NAME}"
    CreateShortcut  "$SMPROGRAMS\${APP_NAME}\${APP_NAME}.lnk" \
                    "$INSTDIR\${APP_EXE}" "" "$INSTDIR\${APP_EXE}" 0
    CreateShortcut  "$SMPROGRAMS\${APP_NAME}\Inspetores.lnk" \
                    "$INSTDIR\Inspetores\Inspetores.exe" "" "$INSTDIR\Inspetores\Inspetores.exe" 0
    CreateShortcut  "$SMPROGRAMS\${APP_NAME}\Painel de Gestao.lnk" \
                    "$INSTDIR\GestaoPainel\GestaoPainel.exe" "" "$INSTDIR\GestaoPainel\GestaoPainel.exe" 0
    CreateShortcut  "$SMPROGRAMS\${APP_NAME}\Desinstalar ${APP_NAME}.lnk" \
                    "$INSTDIR\Uninstall.exe"

    ; Atalho na Área de Trabalho
    CreateShortcut  "$DESKTOP\${APP_NAME}.lnk" \
                    "$INSTDIR\${APP_EXE}" "" "$INSTDIR\${APP_EXE}" 0
    CreateShortcut  "$DESKTOP\Inspetores.lnk" \
                    "$INSTDIR\Inspetores\Inspetores.exe" "" "$INSTDIR\Inspetores\Inspetores.exe" 0
    CreateShortcut  "$DESKTOP\Painel de Gestao.lnk" \
                    "$INSTDIR\GestaoPainel\GestaoPainel.exe" "" "$INSTDIR\GestaoPainel\GestaoPainel.exe" 0

SectionEnd

; ─── Desinstalação ───────────────────────────────────────────────────────────
Section "Uninstall"
    ; Perguntar sobre o banco de dados
    MessageBox MB_YESNO "Deseja manter os dados dos alunos (banco de dados)?$\r$\nClique SIM para manter ou NÃO para apagar tudo." IDYES manter_dados

    ; Apagar tudo incluindo banco
    RMDir /r "$INSTDIR"
    Goto fim_uninstall

    manter_dados:
    ; Copiar banco para documentos antes de apagar
    CopyFiles "$INSTDIR\database\escola.db" "$DOCUMENTS\escola_backup.db"
    MessageBox MB_OK "Seus dados foram salvos em:$\r$\n$DOCUMENTS\escola_backup.db$\r$\nGuarde este arquivo com segurança!"
    RMDir /r "$INSTDIR"

    fim_uninstall:
    ; Remover atalhos
    Delete "$SMPROGRAMS\${APP_NAME}\${APP_NAME}.lnk"
    Delete "$SMPROGRAMS\${APP_NAME}\Desinstalar ${APP_NAME}.lnk"
    RMDir  "$SMPROGRAMS\${APP_NAME}"
    Delete "$DESKTOP\${APP_NAME}.lnk"

    ; Remover registro
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}"

SectionEnd
