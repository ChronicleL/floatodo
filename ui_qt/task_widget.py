"""
FloaTodo — 任务待办列表与条目组件
"""
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QScrollArea, QFrame, QMenu
)
from PySide6.QtGui import QFont, QAction, QColor, QPainter

from ui_qt.styles import (
    BG_HEX, BG_HOVER_HEX, BG_PRESSED_HEX, TEXT_PRI_HEX, TEXT_SEC_HEX, TEXT_MUTED_HEX,
    ACCENT_WORK, COLOR_RED, COLOR_SD, COLOR_SL
)


def fmt_elapsed(seconds: int) -> str:
    m = seconds // 60
    s = seconds % 60
    if m >= 60:
        h = m // 60
        m = m % 60
        return f"{h}h {m}m"
    return f"{m:02d}:{s:02d}"


class TaskItemWidget(QFrame):
    completed_toggled = Signal(int, bool)
    timer_toggled = Signal(int)
    delete_requested = Signal(int)

    def __init__(self, task_id: int, title: str, done: bool = False, elapsed: int = 0, parent=None):
        super().__init__(parent)
        self.task_id = task_id
        self._title = title
        self._done = done
        self._elapsed = elapsed
        self._timer_active = False

        self.setFixedHeight(44)
        self.setCursor(Qt.PointingHandCursor)
        self._init_ui()

    def _init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 4, 10, 4)
        layout.setSpacing(8)

        # 勾选框（拟态凹凸按钮）
        self.chk_btn = QPushButton("✓" if self._done else "")
        self.chk_btn.setFixedSize(22, 22)
        self._update_chk_style()
        self.chk_btn.clicked.connect(self._toggle_done)
        layout.addWidget(self.chk_btn)

        # 任务标题
        self.title_label = QLabel(self._title)
        self._update_title_style()
        layout.addWidget(self.title_label, 1)

        # 耗时时长
        self.elapsed_label = QLabel(fmt_elapsed(self._elapsed))
        self.elapsed_label.setFont(QFont("Consolas", 10))
        self.elapsed_label.setStyleSheet(f"color: {TEXT_MUTED_HEX};")
        layout.addWidget(self.elapsed_label)

        # 独立秒表计时按钮
        self.timer_btn = QPushButton("⏱")
        self.timer_btn.setFixedSize(26, 26)
        self.timer_btn.setToolTip("开启/暂停任务计时")
        self._update_timer_btn_style()
        self.timer_btn.clicked.connect(lambda: self.timer_toggled.emit(self.task_id))
        layout.addWidget(self.timer_btn)

        self._apply_frame_style()

    def _apply_frame_style(self):
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_HEX};
                border-radius: 8px;
            }}
            QFrame:hover {{
                background-color: {BG_HOVER_HEX};
            }}
        """)

    def _update_chk_style(self):
        if self._done:
            self.chk_btn.setText("✓")
            self.chk_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {ACCENT_WORK};
                    color: #FFFFFF;
                    font-size: 11px;
                    font-weight: bold;
                    border-radius: 6px;
                }}
            """)
        else:
            self.chk_btn.setText("")
            self.chk_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: #DEE1E8;
                    border-radius: 6px;
                    border: 1px solid rgba(174, 174, 192, 0.45);
                }}
                QPushButton:hover {{
                    border: 1px solid {ACCENT_WORK};
                }}
            """)

    def _update_title_style(self):
        font = QFont("Segoe UI Variable Display", 10)
        font.setStrikeOut(self._done)
        self.title_label.setFont(font)
        color = TEXT_MUTED_HEX if self._done else TEXT_PRI_HEX
        self.title_label.setStyleSheet(f"color: {color};")

    def _update_timer_btn_style(self):
        if self._timer_active:
            self.timer_btn.setText("⏸")
            self.timer_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {ACCENT_WORK};
                    color: #FFFFFF;
                    border-radius: 6px;
                    font-size: 11px;
                }}
            """)
        else:
            self.timer_btn.setText("⏱")
            self.timer_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {TEXT_MUTED_HEX};
                    border-radius: 6px;
                    font-size: 12px;
                }}
                QPushButton:hover {{
                    background-color: {BG_PRESSED_HEX};
                    color: {TEXT_PRI_HEX};
                }}
            """)

    def _toggle_done(self):
        self._done = not self._done
        self._update_chk_style()
        self._update_title_style()
        self.completed_toggled.emit(self.task_id, self._done)

    def set_elapsed(self, seconds: int):
        self._elapsed = seconds
        self.elapsed_label.setText(fmt_elapsed(seconds))

    def set_timer_active(self, active: bool):
        self._timer_active = active
        self._update_timer_btn_style()

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {BG_HEX};
                border-radius: 8px;
                padding: 4px;
                border: 1px solid rgba(174, 174, 192, 0.3);
            }}
            QMenu::item {{
                padding: 6px 16px;
                border-radius: 5px;
                font-size: 12px;
                color: {TEXT_PRI_HEX};
            }}
            QMenu::item:selected {{
                background-color: {BG_PRESSED_HEX};
            }}
        """)
        del_action = QAction("🗑 删除任务", menu)
        del_action.triggered.connect(lambda: self.delete_requested.emit(self.task_id))
        menu.addAction(del_action)
        menu.exec(event.globalPos())


class TaskListView(QWidget):
    task_added = Signal(str)
    task_completed = Signal(int, bool)
    task_timer_toggled = Signal(int)
    task_deleted = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._task_widgets = {}  # task_id -> TaskItemWidget
        self._active_timer_id = None
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 4, 14, 8)
        layout.setSpacing(6)

        # 头部：标题与添加按钮
        header_layout = QHBoxLayout()
        self.header_label = QLabel("TODAY  (0/0)")
        self.header_label.setFont(QFont("Segoe UI Variable Display", 9, QFont.Bold))
        self.header_label.setStyleSheet(f"color: {TEXT_SEC_HEX}; letter-spacing: 1px;")
        header_layout.addWidget(self.header_label, 1)

        self.btn_toggle_add = QPushButton("＋ 添加")
        self.btn_toggle_add.setFont(QFont("Segoe UI Variable Display", 9))
        self.btn_toggle_add.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {ACCENT_WORK};
                font-weight: bold;
                padding: 2px 6px;
            }}
            QPushButton:hover {{
                color: #5E52A0;
            }}
        """)
        self.btn_toggle_add.clicked.connect(self._toggle_add_bar)
        header_layout.addWidget(self.btn_toggle_add)
        layout.addLayout(header_layout)

        # 添加任务输入框容器（默认隐藏或收起）
        self.add_container = QWidget()
        add_layout = QHBoxLayout(self.add_container)
        add_layout.setContentsMargins(0, 2, 0, 4)
        add_layout.setSpacing(6)

        self.input_task = QLineEdit()
        self.input_task.setPlaceholderText("输入任务名称并按回车...")
        self.input_task.returnPressed.connect(self._submit_task)
        add_layout.addWidget(self.input_task, 1)

        self.btn_submit = QPushButton("添加")
        self.btn_submit.setFixedSize(50, 30)
        self.btn_submit.setStyleSheet(f"""
            QPushButton {{
                background-color: {ACCENT_WORK};
                color: #FFFFFF;
                font-size: 12px;
                font-weight: bold;
                border-radius: 8px;
            }}
            QPushButton:hover {{
                background-color: #6C5EAF;
            }}
        """)
        self.btn_submit.clicked.connect(self._submit_task)
        add_layout.addWidget(self.btn_submit)

        self.add_container.hide()
        layout.addWidget(self.add_container)

        # 滚动列表区域
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setStyleSheet("background: transparent; border: none;")

        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_layout.setSpacing(5)
        self.scroll_layout.addStretch(1)

        self.empty_label = QLabel("暂无待办事项，点击右上角添加 ✨")
        self.empty_label.setAlignment(Qt.AlignCenter)
        self.empty_label.setFont(QFont("Segoe UI Variable Display", 9))
        self.empty_label.setStyleSheet(f"color: {TEXT_MUTED_HEX}; padding: 20px 0;")
        self.scroll_layout.insertWidget(0, self.empty_label)

        self.scroll.setWidget(self.scroll_content)
        layout.addWidget(self.scroll, 1)

    def _toggle_add_bar(self):
        if self.add_container.isHidden():
            self.add_container.show()
            self.input_task.setFocus()
            self.btn_toggle_add.setText("▲ 收起")
        else:
            self.add_container.hide()
            self.btn_toggle_add.setText("＋ 添加")

    def _submit_task(self):
        text = self.input_task.text().strip()
        if text:
            self.task_added.emit(text)
            self.input_task.clear()
            self.add_container.hide()
            self.btn_toggle_add.setText("＋ 添加")

    def update_tasks(self, tasks: list):
        # 清除旧 widgets
        for w in self._task_widgets.values():
            w.setParent(None)
            w.deleteLater()
        self._task_widgets.clear()

        if tasks:
            self.empty_label.hide()
            for t in tasks:
                self.add_task_item(t)
        else:
            self.empty_label.show()

        self._update_header_stats(tasks)

    def add_task_item(self, task):
        self.empty_label.hide()
        w = TaskItemWidget(
            task_id=task.id,
            title=task.title,
            done=task.is_completed,
            elapsed=task.elapsed_seconds,
            parent=self.scroll_content
        )
        w.completed_toggled.connect(self._on_item_completed)
        w.timer_toggled.connect(self._on_item_timer)
        w.delete_requested.connect(self._on_item_delete)

        if self._active_timer_id == task.id:
            w.set_timer_active(True)

        self._task_widgets[task.id] = w
        # 插入到 stretch 之前
        self.scroll_layout.insertWidget(self.scroll_layout.count() - 1, w)

    def update_task_elapsed(self, task_id: int, elapsed: int):
        if task_id in self._task_widgets:
            self._task_widgets[task_id].set_elapsed(elapsed)

    def set_active_timer(self, task_id: int | None):
        self._active_timer_id = task_id
        for tid, w in self._task_widgets.items():
            w.set_timer_active(tid == task_id)

    def _on_item_completed(self, task_id: int, done: bool):
        self.task_completed.emit(task_id, done)

    def _on_item_timer(self, task_id: int):
        self.task_timer_toggled.emit(task_id)

    def _on_item_delete(self, task_id: int):
        if task_id in self._task_widgets:
            w = self._task_widgets.pop(task_id)
            w.setParent(None)
            w.deleteLater()
        self.task_deleted.emit(task_id)
        if not self._task_widgets:
            self.empty_label.show()

    def update_stats(self, total: int, done: int):
        self.header_label.setText(f"TODAY  ({done}/{total})")

    def _update_header_stats(self, tasks: list):
        total = len(tasks)
        done = sum(1 for t in tasks if t.is_completed)
        self.update_stats(total, done)
