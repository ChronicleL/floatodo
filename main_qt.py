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

    # 热键注册放到后台线程，避免主线程阻塞导致 app.exec() 迟迟不启动
    # 回调用 Qt 信号槽方式保证线程安全
    def _register_hotkey():
        try:
            import keyboard
            from PySide6.QtCore import QMetaObject, Qt as _Qt
            keyboard.add_hotkey(
                "ctrl+shift+f",
                lambda: QMetaObject.invokeMethod(
                    window, "_toggle_window_visibility",
                    _Qt.ConnectionType.QueuedConnection
                ),
                suppress=False
            )
        except Exception as e:
            print(f"[FloaTodo] Hotkey register info: {e}")

    import threading
    threading.Thread(target=_register_hotkey, daemon=True).start()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
