# -*- mode: python ; coding: utf-8 -*-
"""
Inspetores.spec — empacota o painel app.py (Streamlit)
Execute com:  pyinstaller Inspetores.spec
"""
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

datas = [
    ('app.py', '.'),          # o código do painel precisa existir como arquivo de verdade
    ('assets', 'assets'),     # logomarca
]
datas += collect_data_files('streamlit')
datas += collect_data_files('pandas')

a = Analysis(
    ['run_inspetores.py'],
    pathex=['.'],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'streamlit',
        'pandas',
        'requests',
    ] + collect_submodules('streamlit')
      + collect_submodules('pandas'),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name='Inspetores',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,   # mantém uma janela de console visível (o Streamlit roda nela)
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/escolagest.ico',
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
    name='Inspetores',
)
