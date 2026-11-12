"""
FloaTodo — 原生无边框拟态标题栏
标题栏统一 26×26 尺寸规格，按钮视觉比例和谐对齐
"""
from PySide6.QtCore import Qt, Signal, QPoint
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QSizePolicy
from PySide6.QtGui import QFont

from ui_qt.styles import (
    BG_HEX, BG_PRESSED_HEX, TEXT_PRI_HEX, TEXT_SEC_HEX, TEXT_MUTED_HEX,
    COLOR_RED
)
from ui_qt.controls import PinButton


class TitleBar(QWidget):
    pin_toggled = Signal(bool)
    mini_clicked = Signal()
    frost_clicked = Signal()      # 毛玻璃皮肤切换
    minimize_clicked = Signal()
    close_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(38)
        self._parent = parent
        self._drag_pos = QPoint()
        self._is_pinned = True
        self._is_mini = False

        self._init_ui()

    def _init_ui(self):
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(12, 0, 8, 0)
        self.layout.setSpacing(3)

        # 🍅 图标
        self.ico_label = QLabel("🍅")
        self.ico_label.setFont(QFont("Segoe UI Emoji", 12))
        self.layout.addWidget(self.ico_label)

        # 标题/阶段文本（支持宽度弹性缩放，不强制顶开父窗体）
        self.title_label = QLabel("专注时间段 (第 1 个/共 4 个)")
        self.title_label.setFont(QFont("Segoe UI Variable Display", 10, QFont.Bold))
        self.title_label.setStyleSheet(f"color: {TEXT_PRI_HEX};")
        self.title_label.setMinimumWidth(0)
        self.title_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.layout.addWidget(self.title_label, 1)

        # 统一的 26×26 按钮样式
        btn_style = f"""
            QPushButton {{
                background-color: transparent;
                color: {TEXT_MUTED_HEX};
                border-radius: 6px;
                font-size: 13px;
                min-width: 26px;
                max-width: 26px;
                min-height: 26px;
                max-height: 26px;
                padding: 0px;
            }}
            QPushButton:hover {{
                background-color: {BG_PRESSED_HEX};
                color: {TEXT_PRI_HEX};
            }}
        """

        # 1. 动态图钉按钮（严格统一 26×26）
        self.btn_pin = PinButton(is_pinned=True, parent=self)
        self.btn_pin.clicked.connect(self._toggle_pin)
        self.layout.addWidget(self.btn_pin)

        # 2. 迷你模式按钮（统一 26×26）
        self.btn_mini = QPushButton("⊟")
        self.btn_mini.setToolTip("切换迷你挂件模式")
        self.btn_mini.setStyleSheet(btn_style)
        self.btn_mini.clicked.connect(self.mini_clicked.emit)
        self.layout.addWidget(self.btn_mini)

        # 2b. 毛玻璃皮肤按钮（统一 26×26）
        self.btn_frost = QPushButton("❄")
        self.btn_frost.setToolTip("切换毛玻璃皮肤")
        self.btn_frost.setStyleSheet(btn_style)
        self.btn_frost.clicked.connect(self.frost_clicked.emit)
        self.layout.addWidget(self.btn_frost)

        # 3. 最小化按钮（统一 26×26）
        self.btn_minimize = QPushButton("—")
        self.btn_minimize.setToolTip("最小化到任务栏")
        self.btn_minimize.setStyleSheet(btn_style)
        self.btn_minimize.clicked.connect(self.minimize_clicked.emit)
        self.layout.addWidget(self.btn_minimize)

        # 4. 关闭按钮（统一 26×26）
        self.btn_close = QPushButton("✕")
        self.btn_close.setToolTip("关闭")
        self.btn_close.setStyleSheet(f"""
            {btn_style}
            QPushButton:hover {{
                background-color: {COLOR_RED};
                color: #FFFFFF;
            }}
        """)
        self.btn_close.clicked.connect(self.close_clicked.emit)
        self.layout.addWidget(self.btn_close)

    def set_stage_text(self, text: str):
        self.title_label.setText(text)

    def set_frost_active(self, active: bool) -> None:
        """更新毛玻璃按钮的激活样式（每次覆盖完整 QSS，避免叠加污染）。"""
        icon_color = "#5E9FF2" if active else TEXT_MUTED_HEX
        self.btn_frost.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {icon_color};
                border-radius: 6px;
                font-size: 13px;
                min-width: 26px; max-width: 26px;
                min-height: 26px; max-height: 26px;
                padding: 0px;
            }}
            QPushButton:hover {{
                background-color: {BG_PRESSED_HEX};
                color: {TEXT_PRI_HEX};
            }}
        """)

    def set_mini_mode(self, is_mini: bool):
        self._is_mini = is_mini
        if is_mini:
            self.btn_mini.setText("⤡")
            self.btn_mini.setToolTip("恢复完整模式")
            self.ico_label.hide()
            self.title_label.hide()
            self.btn_pin.hide()
            self.btn_frost.hide()
            self.btn_minimize.hide()
            self.layout.setContentsMargins(6, 0, 6, 0)
        else:
            self.btn_mini.setText("⊟")
            self.btn_mini.setToolTip("切换迷你挂件模式")
            self.ico_label.show()
            self.title_label.show()
            self.btn_pin.show()
            self.btn_frost.show()
            self.btn_minimize.show()
            self.layout.setContentsMargins(12, 0, 8, 0)

    def _toggle_pin(self):
        self._is_pinned = not self._is_pinned
        self.btn_pin.set_pinned(self._is_pinned)
        self.pin_toggled.emit(self._is_pinned)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self._parent:
            self._drag_pos = event.globalPosition().toPoint() - self._parent.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self._parent and not self._drag_pos.isNull():
            self._parent.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.mini_clicked.emit()
