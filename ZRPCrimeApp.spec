# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['track.py'],
    pathex=[],
    binaries=[],
    datas=[('ZRP_CrimeData.db', '.')],
    hiddenimports=['sklearn', 'sklearn.ensemble', 'pandas', 'fpdf', 'html2image', 'PyQt6.QtWebEngineWidgets'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='ZRPCrimeApp',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
