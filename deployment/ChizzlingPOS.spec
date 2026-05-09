# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['C:\\Users\\Raxell Constantino\\SE CHIZZLING\\SE-Ctrl_Freaks-Chizzling\\src\\LoginPage.py'],
    pathex=[],
    binaries=[],
    datas=[('C:\\Users\\Raxell Constantino\\SE CHIZZLING\\SE-Ctrl_Freaks-Chizzling\\assets', 'assets'), ('C:\\Users\\Raxell Constantino\\SE CHIZZLING\\SE-Ctrl_Freaks-Chizzling\\assets\\food @chizzlin', 'assets/food @chizzlin'), ('C:\\Users\\Raxell Constantino\\SE CHIZZLING\\SE-Ctrl_Freaks-Chizzling\\src', 'src')],
    hiddenimports=['PIL', 'PIL._tkinter_finder', 'tkinter', 'sqlite3', 'matplotlib.backends.backend_tkagg', 'dashboard_views', 'dashboard_db', 'dashboard_charts'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['PyQt5', 'PyQt6', 'PySide2', 'PySide6', 'pytest', 'IPython', 'jupyter', 'notebook', 'scipy', 'pyarrow', 'jedi', 'parso', 'matplotlib.tests', 'numba'],
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
    name='ChizzlingPOS',
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
    icon=['C:\\Users\\Raxell Constantino\\SE CHIZZLING\\SE-Ctrl_Freaks-Chizzling\\assets\\LOGO.ico'],
)
