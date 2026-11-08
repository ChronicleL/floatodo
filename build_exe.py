"""FloaTodo — 轻量化独立 EXE 打包脚本
排除全局环境中庞大的深度学习/科学计算库（如 torch/transformers/cv2 等），
仅打包 PySide6 核心组件与业务模块，保证生成的 exe 轻巧且独立便携。
"""
import sys
import subprocess
import shutil
from pathlib import Path

ROOT = Path(__file__).parent.resolve()

SPEC_CONTENT = f"""# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

# 需要打包的附加数据文件（图标等）
datas = [
    (r'{ROOT / "app.ico"}', '.'),
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
    [r'{ROOT / "main_qt.py"}'],
    pathex=[r'{ROOT}'],
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
    hooksconfig={{}},
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
    icon=r'{ROOT / "app.ico"}',
)
"""

def build():
    spec_file = ROOT / "FloaTodo.spec"
    spec_file.write_text(SPEC_CONTENT, encoding="utf-8")
    print(f"[Build] Spec file created at {spec_file}")

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--clean",
        "--noconfirm",
        str(spec_file)
    ]
    print(f"[Build] Executing: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=str(ROOT))
    if result.returncode == 0:
        exe_path = ROOT / "dist" / "FloaTodo.exe"
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print(f"[Build] SUCCESS! Output: {exe_path} ({size_mb:.2f} MB)")
    else:
        print(f"[Build] FAILED with return code {result.returncode}")

if __name__ == "__main__":
    build()
