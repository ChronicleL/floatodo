"""FloaTodo — 原生 PySide6 入口
"""
import sys
import os
from pathlib import Path

# 添加工程根目录至模块查找路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
import config.settings as settings_mod
from ui_qt.main_window import MainWindow


def main():
    # 启用高 DPI 缩放适配
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # 保持系统托盘常驻

    cfg = settings_mod.load()
    window = MainWindow(cfg)
    window.show()

    # 注册全局唤醒热键 (Ctrl+Shift+F)
    try:
        import keyboard
        import threading
        keyboard.add_hotkey(
            "ctrl+shift+f",
            lambda: window._toggle_window_visibility(),
            suppress=False
        )
    except Exception as e:
        print(f"[FloaTodo] Hotkey register info: {e}")

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
