# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['run_chess_client.py'],
    pathex=[],
    binaries=[],
    datas=[('client', 'client'), ('common', 'common')],
    hiddenimports=['pygame', 'chess', 'chess.engine', 'tkinter', 'tkinter.simpledialog', 'tkinter.messagebox'],
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
    name='Chess',
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
    icon=['client\\assets\\Chess_logo.ico'],
)
