# -*- mode: python ; coding: utf-8 -*-
"""
GestaoPainel.spec — empacota o painel gestao.py (Streamlit)
Execute com:  pyinstaller GestaoPainel.spec
"""
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

datas = [
    ('gestao.py', '.'),
    ('assets', 'assets'),
]
datas += collect_data_files('streamlit')
datas += collect_data_files('pandas')
datas += collect_data_files('plotly')

a = Analysis(
    ['run_gestao.py'],
    pathex=['.'],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'streamlit',
        'pandas',
        'plotly',
        'requests',
    ] + collect_submodules('streamlit')
      + collect_submodules('pandas')
      + collect_submodules('plotly'),
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
    name='GestaoPainel',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
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
    name='GestaoPainel',
)
