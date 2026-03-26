# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for NexLab AI Code Editor.

Build command (from project root D:\\NexLab):
  pyinstaller desktop_app/nexlab.spec --noconfirm

Requirements:
  1. Build the frontend first:  cd desktop_app/frontend && npm run build
  2. Then:  pyinstaller desktop_app/nexlab.spec --noconfirm
  3. Output will be in:  dist/NexLab/NexLab.exe
"""

import os

block_cipher = None

# SPECPATH is a PyInstaller built-in: the directory containing the .spec file
SPEC_DIR = SPECPATH                          # desktop_app/
PROJECT_ROOT = os.path.dirname(SPEC_DIR)     # D:/NexLab/

a = Analysis(
    [os.path.join(SPEC_DIR, 'app.py')],
    pathex=[PROJECT_ROOT, os.path.join(PROJECT_ROOT, 'src')],
    binaries=[],
    datas=[
        # Include the built React frontend
        (os.path.join(SPEC_DIR, 'frontend', 'dist'), os.path.join('desktop_app', 'frontend', 'dist')),
        # Include the smart_agent_arch source package
        (os.path.join(PROJECT_ROOT, 'src', 'smart_agent_arch'), 'smart_agent_arch'),
    ],
    hiddenimports=[
        'uvicorn',
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        'fastapi',
        'starlette',
        'pydantic',
        'smart_agent_arch',
        'smart_agent_arch.user_api',
        'smart_agent_arch.config_loader',
        'smart_agent_arch.model_provider',
        'smart_agent_arch.live_runtime',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['pygame', 'matplotlib', 'PIL', 'numpy', 'scipy', 'pandas', 'tkinter'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# Use --onedir mode (COLLECT) instead of --onefile to avoid MemoryError
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,    # <-- key: binaries go into COLLECT, not EXE
    name='NexLab',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # Enable console for debugging (set to False for release)
    icon=None,      # Set after icon generation
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='NexLab',
)
