# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['wx2md.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'playwright',
        'playwright.sync_api',
        'bs4',
        'markdownify',
        'httpx',
        'frontmatter',
    ],
    excludes=[
        'fastapi',
        'uvicorn',
        'starlette',
        'anyio',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='wx2md-cli',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
