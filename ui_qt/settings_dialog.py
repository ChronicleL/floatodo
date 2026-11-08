"""
FloaTodo — 新拟态风格设置与偏好面板
纯净圆角卡片渲染，去除软件模糊投影导致的边缘截断分层
"""
import os
from pathlib import Path
from PySide6.QtCore import Qt, Signal, QPoint
from PySide6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QSpinBox, QCheckBox, QLineEdit, QFileDialog,
    QFrame, QScrollArea
)
from PySide6.QtGui import QFont, QColor

from ui_qt.styles import (
    BG_HEX, BG_PRESSED_HEX, TEXT_PRI_HEX, TEXT_SEC_HEX, TEXT_MUTED_HEX,
    ACCENT_WORK, COLOR_RED, MAIN_QSS
)
from ui_qt.sound_manager import get_sound_manager


class SettingsDialog(QDialog):
    settings_saved = Signal(dict)

    def __init__(self, current_cfg: dict, parent=None):
        super().__init__(parent)
        self.cfg = dict(current_cfg)
        self._drag_pos = QPoint()
        self._sound_mgr = get_sound_manager()

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.resize(360, 540)
        self.setStyleSheet(MAIN_QSS)

        self._init_ui()
        self._load_values()

    def _init_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)

        # 纯净新拟态卡片背景（无边缘模糊截断）
        card = QFrame(self)
        card.setObjectName("settingsCard")
        card.setStyleSheet(f"""
            QFrame#settingsCard {{
                background-color: {BG_HEX};
                border-radius: 16px;
                border: 1px solid rgba(174, 174, 192, 0.45);
            }}
        """)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 14, 18, 16)
        layout.setSpacing(12)

        # 1. 标题栏
        tb_layout = QHBoxLayout()
        title = QLabel("⚙️  偏好设置")
        title.setFont(QFont("Segoe UI Variable Display", 11, QFont.Bold))
        title.setStyleSheet(f"color: {TEXT_PRI_HEX};")
        tb_layout.addWidget(title, 1)

        btn_close = QPushButton("✕")
        btn_close.setFixedSize(26, 26)
        btn_close.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {TEXT_MUTED_HEX};
                border-radius: 6px;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: {COLOR_RED};
                color: #FFFFFF;
            }}
        """)
        btn_close.clicked.connect(self.reject)
        tb_layout.addWidget(btn_close)
        layout.addLayout(tb_layout)

        # 2. 滚动区域（包含设置项）
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("background: transparent; border: none;")

        content = QWidget()
        form_layout = QVBoxLayout(content)
        form_layout.setContentsMargins(0, 0, 4, 0)
        form_layout.setSpacing(14)

        # ── 分组 1：专注与休息时长 ───────────────────────────
        g1_title = QLabel("⏱  专注与阶段设置")
        g1_title.setFont(QFont("Segoe UI Variable Display", 9, QFont.Bold))
        g1_title.setStyleSheet(f"color: {ACCENT_WORK}; letter-spacing: 0.5px;")
        form_layout.addWidget(g1_title)

        spin_style = f"""
            QSpinBox {{
                background-color: #DEE1E8;
                color: {TEXT_PRI_HEX};
                border-radius: 6px;
                padding: 4px 8px;
                font-size: 12px;
                min-width: 70px;
                border: 1px solid rgba(174, 174, 192, 0.4);
            }}
            QSpinBox:focus {{
                border: 1px solid {ACCENT_WORK};
            }}
        """

        self.spin_rounds = QSpinBox()
        self.spin_rounds.setRange(2, 12)
        self.spin_rounds.setSuffix(" 轮")
        self.spin_rounds.setStyleSheet(spin_style)
        form_layout.addLayout(self._make_row("完整专注轮数：", self.spin_rounds, "完成该轮数后长休并奖励 1 个番茄"))

        self.spin_work = QSpinBox()
        self.spin_work.setRange(1, 120)
        self.spin_work.setSuffix(" 分钟")
        self.spin_work.setStyleSheet(spin_style)
        form_layout.addLayout(self._make_row("专注时长：", self.spin_work, "单次专注时间（默认 25 分钟）"))

        self.spin_short = QSpinBox()
        self.spin_short.setRange(1, 60)
        self.spin_short.setSuffix(" 分钟")
        self.spin_short.setStyleSheet(spin_style)
        form_layout.addLayout(self._make_row("小休息时段：", self.spin_short, "每段专注后的小憩时长（默认 5 分钟）"))

        self.spin_long = QSpinBox()
        self.spin_long.setRange(1, 120)
        self.spin_long.setSuffix(" 分钟")
        self.spin_long.setStyleSheet(spin_style)
        form_layout.addLayout(self._make_row("大休息时段：", self.spin_long, "大满贯后的大休息时长（默认 15 分钟）"))

        # ── 分组 2：音效设置 ─────────────────────────────────
        div = QFrame()
        div.setFixedHeight(1)
        div.setStyleSheet("background-color: rgba(174, 174, 192, 0.3); margin: 4px 0;")
        form_layout.addWidget(div)

        g2_title = QLabel("🔔  音效提示与自主导入")
        g2_title.setFont(QFont("Segoe UI Variable Display", 9, QFont.Bold))
        g2_title.setStyleSheet(f"color: {ACCENT_WORK}; letter-spacing: 0.5px;")
        form_layout.addWidget(g2_title)

        self.chk_sound = QCheckBox("开启声音提示")
        self.chk_sound.setFont(QFont("Segoe UI Variable Display", 10))
        self.chk_sound.setStyleSheet(f"""
            QCheckBox {{
                color: {TEXT_PRI_HEX};
                spacing: 8px;
            }}
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
                border-radius: 4px;
                border: 1px solid rgba(174, 174, 192, 0.5);
                background-color: #DEE1E8;
            }}
            QCheckBox::indicator:checked {{
                background-color: {ACCENT_WORK};
                border: 1px solid {ACCENT_WORK};
            }}
        """)
        form_layout.addWidget(self.chk_sound)

        self.spin_duration = QSpinBox()
        self.spin_duration.setRange(1, 15)
        self.spin_duration.setSuffix(" 秒")
        self.spin_duration.setStyleSheet(spin_style)
        form_layout.addLayout(self._make_row("播放时长上限：", self.spin_duration, "超时自动卡断，防止导入长音乐持续打扰"))

        self.edit_sound_next = QLineEdit()
        self.edit_sound_next.setReadOnly(True)
        self.edit_sound_next.setPlaceholderText("系统默认音效（Windows Asterisk）")
        form_layout.addLayout(self._make_audio_row("阶段流转音效：", self.edit_sound_next, is_done=False))

        self.edit_sound_done = QLineEdit()
        self.edit_sound_done.setReadOnly(True)
        self.edit_sound_done.setPlaceholderText("系统默认音效（Windows Exclamation）")
        form_layout.addLayout(self._make_audio_row("大满贯完成音效：", self.edit_sound_done, is_done=True))

        form_layout.addStretch(1)
        scroll.setWidget(content)
        layout.addWidget(scroll, 1)

        # 3. 底部操作按钮
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(10)

        btn_reset = QPushButton("恢复默认")
        btn_reset.setFixedHeight(34)
        btn_reset.setStyleSheet(f"""
            QPushButton {{
                background-color: #DEE1E8;
                color: {TEXT_SEC_HEX};
                border-radius: 8px;
                font-size: 12px;
                padding: 0 14px;
            }}
            QPushButton:hover {{
                background-color: {BG_PRESSED_HEX};
                color: {TEXT_PRI_HEX};
            }}
        """)
        btn_reset.clicked.connect(self._reset_defaults)
        bottom_layout.addWidget(btn_reset)

        bottom_layout.addStretch(1)

        btn_cancel = QPushButton("取消")
        btn_cancel.setFixedHeight(34)
        btn_cancel.setStyleSheet(f"""
            QPushButton {{
                background-color: #DEE1E8;
                color: {TEXT_PRI_HEX};
                border-radius: 8px;
                font-size: 12px;
                padding: 0 16px;
            }}
            QPushButton:hover {{
                background-color: {BG_PRESSED_HEX};
            }}
        """)
        btn_cancel.clicked.connect(self.reject)
        bottom_layout.addWidget(btn_cancel)

        btn_save = QPushButton("保存设置")
        btn_save.setFixedHeight(34)
        btn_save.setStyleSheet(f"""
            QPushButton {{
                background-color: {ACCENT_WORK};
                color: #FFFFFF;
                border-radius: 8px;
                font-size: 12px;
                font-weight: bold;
                padding: 0 20px;
            }}
            QPushButton:hover {{
                background-color: #6C5EAF;
            }}
        """)
        btn_save.clicked.connect(self._save_settings)
        bottom_layout.addWidget(btn_save)

        layout.addLayout(bottom_layout)
        root_layout.addWidget(card)

    def _make_row(self, label_text: str, widget: QWidget, hint: str = "") -> QHBoxLayout:
        row = QHBoxLayout()
        col = QVBoxLayout()
        lbl = QLabel(label_text)
        lbl.setFont(QFont("Segoe UI Variable Display", 9, QFont.Bold))
        lbl.setStyleSheet(f"color: {TEXT_PRI_HEX};")
        col.addWidget(lbl)
        if hint:
            ht = QLabel(hint)
            ht.setFont(QFont("Segoe UI Variable Display", 8))
            ht.setStyleSheet(f"color: {TEXT_MUTED_HEX};")
            col.addWidget(ht)
        row.addLayout(col, 1)
        row.addWidget(widget)
        return row

    def _make_audio_row(self, label_text: str, line_edit: QLineEdit, is_done: bool) -> QVBoxLayout:
        col = QVBoxLayout()
        col.setSpacing(4)
        lbl = QLabel(label_text)
        lbl.setFont(QFont("Segoe UI Variable Display", 9, QFont.Bold))
        lbl.setStyleSheet(f"color: {TEXT_PRI_HEX};")
        col.addWidget(lbl)

        h = QHBoxLayout()
        h.setSpacing(6)
        h.addWidget(line_edit, 1)

        btn_browse = QPushButton("浏览...")
        btn_browse.setFixedSize(54, 28)
        btn_browse.setStyleSheet(f"""
            QPushButton {{
                background-color: #DEE1E8;
                color: {TEXT_PRI_HEX};
                border-radius: 6px;
                font-size: 11px;
            }}
            QPushButton:hover {{ background-color: {BG_PRESSED_HEX}; }}
        """)
        btn_browse.clicked.connect(lambda: self._browse_audio(line_edit))
        h.addWidget(btn_browse)

        btn_test = QPushButton("▶ 试听")
        btn_test.setFixedSize(50, 28)
        btn_test.setStyleSheet(f"""
            QPushButton {{
                background-color: #DEE1E8;
                color: {ACCENT_WORK};
                font-weight: bold;
                border-radius: 6px;
                font-size: 11px;
            }}
            QPushButton:hover {{ background-color: {BG_PRESSED_HEX}; }}
        """)
        btn_test.clicked.connect(lambda: self._test_audio(line_edit.text()))
        h.addWidget(btn_test)

        btn_clear = QPushButton("✕")
        btn_clear.setFixedSize(26, 28)
        btn_clear.setToolTip("恢复为系统默认音效")
        btn_clear.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {TEXT_MUTED_HEX};
                border-radius: 6px;
                font-size: 12px;
            }}
            QPushButton:hover {{ color: {COLOR_RED}; background-color: {BG_PRESSED_HEX}; }}
        """)
        btn_clear.clicked.connect(lambda: line_edit.clear())
        h.addWidget(btn_clear)

        col.addLayout(h)
        return col

    def _load_values(self):
        self.spin_rounds.setValue(self.cfg.get("pomodoro_long_every", 4))
        self.spin_work.setValue(self.cfg.get("pomodoro_work", 25))
        self.spin_short.setValue(self.cfg.get("pomodoro_short", 5))
        self.spin_long.setValue(self.cfg.get("pomodoro_long", 15))

        self.chk_sound.setChecked(self.cfg.get("sound_enabled", True))
        self.spin_duration.setValue(self.cfg.get("sound_max_duration", 3))

        self.edit_sound_next.setText(self.cfg.get("sound_custom_next", ""))
        self.edit_sound_done.setText(self.cfg.get("sound_custom_done", ""))

    def _browse_audio(self, target_edit: QLineEdit):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "选择提示音频文件",
            "",
            "音频文件 (*.wav *.mp3 *.m4a *.flac *.ogg *.aac);;所有文件 (*.*)"
        )
        if path:
            target_edit.setText(path)

    def _test_audio(self, path: str):
        path = path.strip()
        max_sec = self.spin_duration.value()
        if path and os.path.exists(path):
            self._sound_mgr.play_file(path, max_sec)
        else:
            self._sound_mgr.play("next", {"sound_enabled": True})

    def _reset_defaults(self):
        self.spin_rounds.setValue(4)
        self.spin_work.setValue(25)
        self.spin_short.setValue(5)
        self.spin_long.setValue(15)
        self.chk_sound.setChecked(True)
        self.spin_duration.setValue(3)
        self.edit_sound_next.clear()
        self.edit_sound_done.clear()

    def _save_settings(self):
        self._sound_mgr.stop()
        self.cfg["pomodoro_long_every"] = self.spin_rounds.value()
        self.cfg["pomodoro_work"] = self.spin_work.value()
        self.cfg["pomodoro_short"] = self.spin_short.value()
        self.cfg["pomodoro_long"] = self.spin_long.value()

        self.cfg["sound_enabled"] = self.chk_sound.isChecked()
        self.cfg["sound_max_duration"] = self.spin_duration.value()
        self.cfg["sound_custom_next"] = self.edit_sound_next.text().strip()
        self.cfg["sound_custom_done"] = self.edit_sound_done.text().strip()

        self.settings_saved.emit(self.cfg)
        self.accept()

    def reject(self):
        self._sound_mgr.stop()
        super().reject()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and not self._drag_pos.isNull():
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()
