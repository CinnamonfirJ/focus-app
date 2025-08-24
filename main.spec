# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
<<<<<<< HEAD
    datas=[],
=======
    datas=[('assets', 'assets'), ('backend/process_map.json', 'backend')],
>>>>>>> 24f291e16fc3251e9550ec88d329555712781de1
    hiddenimports=[],
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
    name='main',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
<<<<<<< HEAD
    console=True,
=======
    console=False,
>>>>>>> 24f291e16fc3251e9550ec88d329555712781de1
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
<<<<<<< HEAD
=======
    icon=['assets\\cat_icon.ico'],
>>>>>>> 24f291e16fc3251e9550ec88d329555712781de1
)
