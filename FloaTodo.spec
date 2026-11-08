# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

# 需要打包的附加数据文件（图标等）
datas = [
    (r'D:\pyproject\tomato\app.ico', '.'),
]

# 严格排除全局无关的巨型第三方库，保证 exe 轻量化
excludes = [
    'torch', 'torchvision', 'torchaudio', 'torchao', 'torchcodec', 'torchdiffeq', 'torchsde',
    'transformers', 'scipy', 'matplotlib', 'cv2', 'PIL', 'pandas', 'numpy',
    'gradio', 'uvicorn', 'fastapi', 'tensorboard', 'sklearn', 'scikit-learn',
    'timm', 'einops', 'diffusers', 'kornia', 'paddle', 'paddlex', 'open_clip',
    'pywebview', 'webview', 'clr', 'pythonnet',
    'PySide6.QtWebEngine', 'PySide6.QtWebEngineCore', 'PySide6.QtWebEngineWidgets',
    'PySide6.QtQml', 'PySide6.QtQuick', 'PySide6.QtQuickWidgets', 'PySide6.Qt3DCore',
    'PySide6.QtDesigner', 'PySide6.QtTest', 'PySide6.QtSql', 'PySide6.QtPdf', 'PySide6.QtPdfWidgets',
    'PySide6.QtSvg', 'PySide6.QtSvgWidgets'
]

a = Analysis(
    [r'D:\pyproject\tomato\main_qt.py'],
    pathex=[r'D:\pyproject\tomato'],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'ui_qt', 'ui_qt.main_window', 'ui_qt.focus_dial', 'ui_qt.task_widget',
        'ui_qt.title_bar', 'ui_qt.controls', 'ui_qt.settings_dialog',
        'ui_qt.sound_manager', 'ui_qt.styles',
        'core', 'core.pomodoro', 'core.task_manager', 'core.task_timer',
        'core.models', 'core.signal',
        'config', 'config.settings',
        'utils', 'utils.db',
        'winsound', 'sqlite3', 'keyboard',
        'PySide6.QtNetwork', 'PySide6.QtMultimedia'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='FloaTodo',
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
    icon=r'D:\pyproject\tomato\app.ico',
)
