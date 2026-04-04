# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for Cyber Survivor
# Build with:  pyinstaller cyber_survivor.spec --clean --noconfirm

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        # Include assets folder (fonts/sprites/sounds subdirs, currently placeholder)
        ('assets', 'assets'),
    ],
    hiddenimports=[
        # numpy submodules that PyInstaller sometimes misses
        'numpy',
        'numpy.core._multiarray_umath',
        'numpy.random',
        'numpy.fft',
        'pygame',
        'pygame.mixer',
        'pygame.sndarray',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    # Exclude heavy packages that are definitely not used
    excludes=[
        'tkinter',
        'matplotlib',
        'scipy',
        'PIL',
        'cv2',
        'IPython',
        'jupyter',
        'xmlrpc',
        'test',
        'unittest',
        'pydoc',
    ],
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
    name='CyberSurvivor',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,   # no console window — game-only
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,       # set to 'icon.ico' if you add an icon later
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='CyberSurvivor',
)
