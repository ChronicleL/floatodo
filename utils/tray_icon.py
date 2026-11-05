"""系统托盘图标"""
from __future__ import annotations
from pathlib import Path

from PySide6.QtCore import QObject
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QFont, QAction
from PySide6.QtWidgets import QSystemTrayIcon, QMenu, QApplication


def _make_tray_icon() -> QIcon:
    """动态生成一个简单的番茄图标（16x16）"""
    pix = QPixmap(32, 32)
    pix.fill(QColor(0, 0, 0, 0))
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    # 绘制圆形背景
    painter.setBrush(QColor("#E8EAF0"))
    painter.setPen(QColor("#C8CAD4"))
    painter.drawEllipse(2, 2, 28, 28)
    # 绘制 emoji 文字
    painter.setFont(QFont("Segoe UI Emoji", 16))
    painter.setPen(QColor("#2D3748"))
    painter.drawText(pix.rect(), 0x84, "🍅")  # Qt.AlignCenter
    painter.end()
    return QIcon(pix)


class TrayIcon(QObject):
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self._window = main_window

        icon = _make_tray_icon()
        self._tray = QSystemTrayIcon(icon, self)
        self._tray.setToolTip("FloaTodo — 悬浮待办清单")

        menu = QMenu()
        show_action = QAction("显示/隐藏", menu)
        show_action.triggered.connect(self._toggle_window)

        quit_action = QAction("退出", menu)
        quit_action.triggered.connect(QApplication.quit)

        menu.addAction(show_action)
        menu.addSeparator()
        menu.addAction(quit_action)

        self._tray.setContextMenu(menu)
        self._tray.activated.connect(self._on_activated)
        self._tray.show()

    def _toggle_window(self) -> None:
        if self._window.isVisible():
            self._window.hide()
        else:
            self._window.show()
            self._window.raise_()
            self._window.activateWindow()

    def _on_activated(self, reason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._toggle_window()

    def show_message(self, title: str, msg: str) -> None:
        self._tray.showMessage(title, msg, QSystemTrayIcon.MessageIcon.Information, 3000)
