# -*- mode: python ; coding: utf-8 -*-
"""
EscolaGest.spec — Configuração do PyInstaller
Execute com:  pyinstaller EscolaGest.spec
"""

import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Coletar todos os dados necessários
datas = [
    ('assets',   'assets'),    # logomarca e ícone
    ('modules',  'modules'),   # módulos do sistema
    ('database', 'database'),  # pasta do banco (sem o .db - ele é criado no primeiro uso)
]

# Coletar dados do customtkinter (temas, imagens internas)
datas += collect_data_files('customtkinter')

# Coletar dados do reportlab (fontes e recursos)
datas += collect_data_files('reportlab')

# Coletar dados do docxtpl (usado nos requerimentos SEED) e suas dependências
datas += collect_data_files('docxtpl')
datas += collect_data_files('docx')  # python-docx

# SofIA / RAG (busca em documentos) - sentence-transformers puxa torch e
# transformers junto, então isso deixa o instalador BEM maior (pode passar
# de 1 GB). É esperado.
datas += collect_data_files('sentence_transformers')
datas += collect_data_files('transformers')
datas += collect_data_files('torch')
datas += collect_data_files('numpy')
datas += collect_data_files('pypdf')
datas += collect_data_files('pandas')
datas += collect_data_files('openpyxl')

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'customtkinter',
        'tkinter',
        'tkinter.ttk',
        'tkinter.messagebox',
        'tkinter.filedialog',
        'PIL',
        'PIL.Image',
        'PIL.ImageTk',
        'reportlab',
        'reportlab.lib',
        'reportlab.lib.pagesizes',
        'reportlab.lib.units',
        'reportlab.lib.colors',
        'reportlab.lib.styles',
        'reportlab.lib.enums',
        'reportlab.platypus',
        'reportlab.platypus.tables',
        'sqlite3',
        'webbrowser',
        're',
        'os',
        'sys',
        'datetime',
        'tempfile',
        'subprocess',
        # Geração dos boletins/requerimentos em Word (BF e formulários SEED)
        'docx',
        'docxtpl',
        'jinja2',
        'lxml',
        'lxml.etree',
        'markupsafe',
        'typing_extensions',
        # Geração de PDF (relatórios antigos / diplomas)
        'fpdf',
        'fpdf2',
        # IA para redação de ofícios/atas/bilhetes
        'groq',
        # Sincronização com a nuvem (Supabase)
        'requests',
        # SofIA / RAG
        'sentence_transformers',
        'transformers',
        'torch',
        'numpy',
        'pypdf',
        'fitz',
        'pymupdf',
        'xlrd',
        'openpyxl',
        'pandas',
    ] + collect_submodules('customtkinter')
      + collect_submodules('reportlab')
      + collect_submodules('docx')
      + collect_submodules('docxtpl')
      + collect_submodules('lxml')
      + collect_submodules('sentence_transformers')
      + collect_submodules('transformers'),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib', 'scipy'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='JoaoOSecretario',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,          # Sem janela preta de console
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/escolagest.ico',    # Ícone do executável
    version_info=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='JoaoOSecretario',
)
