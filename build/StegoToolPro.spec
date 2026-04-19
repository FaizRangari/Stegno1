# -*- mode: python ; coding: utf-8 -*-

import os

project_root = os.path.abspath(os.getcwd())

a = Analysis(
    [os.path.join(project_root, 'app', 'main.py')],
    pathex=[project_root],
    binaries=[],
    datas=[
        (os.path.join(project_root, 'ui'), 'ui'),
        (os.path.join(project_root, 'assets'), 'assets'),
    ],
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
    name="StegoToolPro",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(project_root, 'assets', 'logo.ico'),
    version=os.path.join(project_root, 'build', 'version_info.txt'),
)
