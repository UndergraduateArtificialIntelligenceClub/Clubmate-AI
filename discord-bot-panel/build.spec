# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all
import sys
import os

block_cipher = None

# Collect hidden imports for libraries that use dynamic loading
datas = []
binaries = []
hiddenimports = [
    'uvicorn.logging', 
    'uvicorn.loops', 
    'uvicorn.loops.auto', 
    'uvicorn.protocols', 
    'uvicorn.protocols.http', 
    'uvicorn.protocols.http.auto', 
    'uvicorn.lifespan', 
    'uvicorn.lifespan.on', 
    'engineio.async_drivers.aiohttp', 
    'sqlmodel', 
    'asyncpg',
    'app.routers.auth',
    'app.routers.api_keys'
]

# Collect metadata for key packages
tmp_ret = collect_all('uvicorn')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]

tmp_ret = collect_all('fastapi')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]

a = Analysis(
    ['gui.py'],
    pathex=[],
    binaries=binaries,
    datas=datas + [
        ('frontend/dist', 'frontend/dist'),  # Include React Build
        ('backend/app', 'app'),              # Include Backend Source
        ('.env', '.')                        # Include .env (Manual copy needed usually)
    ],
    hiddenimports=hiddenimports,
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
    name='DiscordBotPanel',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False, # Set True to see errors during dev builds
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='DiscordBotPanel',
)
