# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

# 需要打包的附加数据文件（图标等）
datas = [
    (r'E:\py-project\temp\floatodo\app.ico', '.'),
]

# 严格排除全局无关的巨型第三方库，保证 exe 轻量化
excludes = [
    # ── 深度学习 / 科学计算（环境里存在但与本项目完全无关）────────────────
    'torch', 'torchvision', 'torchaudio', 'torchao', 'torchcodec', 'torchdiffeq', 'torchsde',
    'transformers', 'scipy', 'matplotlib', 'cv2', 'PIL', 'pandas', 'numpy',
    'gradio', 'uvicorn', 'fastapi', 'tensorboard', 'sklearn', 'scikit-learn',
    'timm', 'einops', 'diffusers', 'kornia', 'paddle', 'paddlex', 'open_clip',
    # ── 旧版 webview 依赖 ─────────────────────────────────────────────────
    'pywebview', 'webview', 'clr', 'pythonnet',
    # ── 未用到的 Qt 子模块（每个可节省 0.1–8 MB）─────────────────────────
    'PySide6.QtWebEngine', 'PySide6.QtWebEngineCore', 'PySide6.QtWebEngineWidgets',
    'PySide6.QtWebEngineQuick', 'PySide6.QtWebChannel', 'PySide6.QtWebSockets',
    'PySide6.QtQml', 'PySide6.QtQuick', 'PySide6.QtQuickWidgets', 'PySide6.QtQuickControls2',
    'PySide6.Qt3DCore', 'PySide6.Qt3DInput', 'PySide6.Qt3DLogic',
    'PySide6.Qt3DAnimation', 'PySide6.Qt3DExtras', 'PySide6.Qt3DRender',
    'PySide6.QtDesigner', 'PySide6.QtUiTools',
    'PySide6.QtTest', 'PySide6.QtSql', 'PySide6.QtDBus',
    'PySide6.QtPdf', 'PySide6.QtPdfWidgets',
    'PySide6.QtSvg', 'PySide6.QtSvgWidgets',
    'PySide6.QtXml', 'PySide6.QtHelp', 'PySide6.QtPrintSupport',
    'PySide6.QtConcurrent', 'PySide6.QtShaderTools',
    'PySide6.QtSpatialAudio', 'PySide6.QtCharts', 'PySide6.QtDataVisualization',
    'PySide6.QtBluetooth', 'PySide6.QtNfc', 'PySide6.QtSerialPort',
    'PySide6.QtLocation', 'PySide6.QtPositioning',
    # ── 其他不需要的标准库模块 ─────────────────────────────────────────────
    'tkinter', 'unittest', 'xmlrpc', 'ftplib', 'imaplib', 'poplib',
    'smtplib', 'email', 'html', 'http.server', 'urllib.robotparser',
]

a = Analysis(
    [r'E:\py-project\temp\floatodo\main_qt.py'],
    pathex=[r'E:\py-project\temp\floatodo'],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'ui_qt', 'ui_qt.main_window', 'ui_qt.focus_dial', 'ui_qt.task_widget',
        'ui_qt.title_bar', 'ui_qt.controls', 'ui_qt.settings_dialog',
        'ui_qt.sound_manager', 'ui_qt.styles', 'ui_qt.window_effects',
        'core', 'core.pomodoro', 'core.task_manager', 'core.task_timer',
        'core.models', 'core.signal',
        'config', 'config.settings',
        'utils', 'utils.db',
        'winsound', 'sqlite3', 'keyboard',
        # QtNetwork 和 QtMultimedia 是可选依赖，sound_manager.py 已做 try/except
        # 不加入 hiddenimports 可减少约 2-3 MB
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
    icon=r'E:\py-project\temp\floatodo\app.ico',
)
