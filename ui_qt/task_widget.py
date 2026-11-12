"""
FloaTodo — 任务待办列表与条目组件
支持拖拽排序和右键编辑
"""
from PySide6.QtCore import Qt, Signal, QMimeData, QPoint
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QScrollArea, QFrame, QMenu, QApplication
)
from PySide6.QtGui import (
    QFont, QAction, QColor, QPainter, QPen, QDrag, QPixmap
)

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
    timer_toggled     = Signal(int)
    delete_requested  = Signal(int)
    edit_requested    = Signal(int, str)   # task_id, new_title

    def __init__(self, task_id: int, title: str, done: bool = False,
                 elapsed: int = 0, parent=None):
        super().__init__(parent)
        self.task_id = task_id
        self._title  = title
        self._done   = done
        self._elapsed = elapsed
        self._timer_active  = False
        self._drag_start_pos = None   # 拖拽起始点（None = 非手柄区域按下）
        self._edit_input: QLineEdit | None = None
        self._editing = False          # 防止 editingFinished 双触发

        self.setFixedHeight(44)
        self.setCursor(Qt.PointingHandCursor)
        self.setMouseTracking(True)
        self._init_ui()

    # ── UI 构建 ───────────────────────────────────────────────────────
    def _init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 4, 10, 4)
        layout.setSpacing(6)

        # 拖拽手柄
        self.drag_handle = QLabel("⠿")
        self.drag_handle.setFixedWidth(14)
        self.drag_handle.setAlignment(Qt.AlignCenter)
        self.drag_handle.setCursor(Qt.SizeVerCursor)
        self.drag_handle.setToolTip("拖拽排列顺序")
        self.drag_handle.setStyleSheet(f"color: {TEXT_MUTED_HEX}; font-size: 11px;")
        layout.addWidget(self.drag_handle)

        # 勾选框
        self.chk_btn = QPushButton("✓" if self._done else "")
        self.chk_btn.setFixedSize(22, 22)
        self._update_chk_style()
        self.chk_btn.clicked.connect(self._toggle_done)
        layout.addWidget(self.chk_btn)

        # 任务标题
        self.title_label = QLabel(self._title)
        self._update_title_style()
        layout.addWidget(self.title_label, 1)

        # 耗时
        self.elapsed_label = QLabel(fmt_elapsed(self._elapsed))
        self.elapsed_label.setFont(QFont("Consolas", 10))
        self.elapsed_label.setStyleSheet(f"color: {TEXT_MUTED_HEX};")
        layout.addWidget(self.elapsed_label)

        # 计时按钮
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

    # ── 拖拽排序 ──────────────────────────────────────────────────────
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            pt = event.position().toPoint()
            # 只有点在拖拽手柄区域才允许拖拽
            if self.drag_handle.geometry().contains(pt):
                self._drag_start_pos = pt
            else:
                self._drag_start_pos = None
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if (self._drag_start_pos is not None and
                (event.buttons() & Qt.LeftButton)):
            dist = (event.position().toPoint() - self._drag_start_pos).manhattanLength()
            if dist >= QApplication.startDragDistance():
                self._do_drag()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_start_pos = None
        super().mouseReleaseEvent(event)

    def _do_drag(self):
        self._drag_start_pos = None   # 防止重入

        drag = QDrag(self)
        mime = QMimeData()
        mime.setText(f"floatodo_task:{self.task_id}")
        drag.setMimeData(mime)

        # 半透明截图作为拖拽图标
        raw = self.grab()
        ghost = QPixmap(raw.size())
        ghost.fill(Qt.transparent)
        p = QPainter(ghost)
        p.setOpacity(0.65)
        p.drawPixmap(0, 0, raw)
        p.end()
        drag.setPixmap(ghost)
        drag.setHotSpot(QPoint(raw.width() // 2, raw.height() // 2))

        drag.exec(Qt.MoveAction)

    # ── 右键菜单（编辑 + 删除）────────────────────────────────────────
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
            QMenu::separator {{
                height: 1px;
                background: rgba(174, 174, 192, 0.3);
                margin: 2px 8px;
            }}
        """)

        edit_action = QAction("✏️ 编辑任务名称", menu)
        edit_action.triggered.connect(self._start_inline_edit)
        menu.addAction(edit_action)

        menu.addSeparator()

        del_action = QAction("🗑 删除任务", menu)
        del_action.triggered.connect(lambda: self.delete_requested.emit(self.task_id))
        menu.addAction(del_action)

        menu.exec(event.globalPos())

    # ── 内联编辑 ──────────────────────────────────────────────────────
    def _start_inline_edit(self):
        if self._editing:
            return
        self._editing = True

        if self._edit_input is None:
            self._edit_input = QLineEdit(self)
            self._edit_input.setFrame(False)
            self._edit_input.setFont(QFont("Segoe UI Variable Display", 10))
            self._edit_input.setStyleSheet(f"""
                QLineEdit {{
                    background: transparent;
                    border: none;
                    border-bottom: 1.5px solid {ACCENT_WORK};
                    color: {TEXT_PRI_HEX};
                    padding: 0px;
                }}
            """)
            self._edit_input.editingFinished.connect(self._finish_edit)

        self._edit_input.setGeometry(self.title_label.geometry())
        self._edit_input.setText(self._title)
        self.title_label.hide()
        self._edit_input.show()
        self._edit_input.raise_()
        self._edit_input.selectAll()
        self._edit_input.setFocus()

    def _finish_edit(self):
        if not self._editing:
            return
        self._editing = False

        if self._edit_input is None:
            return

        new_title = self._edit_input.text().strip()
        self._edit_input.hide()
        self.title_label.show()

        if new_title and new_title != self._title:
            self._title = new_title
            self.title_label.setText(new_title)
            self._update_title_style()
            self.edit_requested.emit(self.task_id, new_title)


# ── 支持拖拽的滚动内容容器 ──────────────────────────────────────────────
class _TaskDropArea(QWidget):
    """接收 TaskItemWidget 拖拽事件，显示插入位置指示线并触发排序信号。"""
    item_dropped = Signal(int, int)   # (task_id, layout_target_index)

    _INDICATOR = QColor("#7B68EE")

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self._indicator_y = -1

    def dragEnterEvent(self, event):
        if (event.mimeData().hasText() and
                event.mimeData().text().startswith("floatodo_task:")):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        self._indicator_y = self._indicator_pos_y(event.position().toPoint())
        self.update()
        event.acceptProposedAction()

    def dragLeaveEvent(self, event):
        self._indicator_y = -1
        self.update()

    def dropEvent(self, event):
        self._indicator_y = -1
        self.update()
        txt = event.mimeData().text()
        if not txt.startswith("floatodo_task:"):
            return
        task_id = int(txt.split(":")[-1])
        idx = self._drop_index(event.position().toPoint())
        event.acceptProposedAction()
        self.item_dropped.emit(task_id, idx)

    def paintEvent(self, event):
        super().paintEvent(event)
        if self._indicator_y < 0:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setPen(QPen(self._INDICATOR, 2))
        p.drawLine(16, self._indicator_y, self.width() - 8, self._indicator_y)
        p.setBrush(self._INDICATOR)
        p.setPen(Qt.NoPen)
        p.drawEllipse(8, self._indicator_y - 3, 6, 6)

    def _drop_index(self, pos) -> int:
        """返回拖入目标在 layout 中的插入位置索引（stretch 之前）。"""
        layout = self.layout()
        if layout is None:
            return 0
        # layout 末尾是 stretch，task widget 在 count-1 个
        for i in range(layout.count() - 1):
            item = layout.itemAt(i)
            w = item.widget() if item else None
            if w is None:
                continue
            if pos.y() < w.geometry().y() + w.height() // 2:
                return i
        return layout.count() - 1   # 最后一个 task widget 之后 / stretch 之前

    def _indicator_pos_y(self, pos) -> int:
        layout = self.layout()
        if layout is None:
            return pos.y()
        for i in range(layout.count() - 1):
            item = layout.itemAt(i)
            w = item.widget() if item else None
            if w is None:
                continue
            if pos.y() < w.geometry().y() + w.height() // 2:
                return max(0, w.geometry().top() - 2)
        # 最后一个 task widget 下边缘
        for i in range(layout.count() - 2, -1, -1):
            item = layout.itemAt(i)
            w = item.widget() if item else None
            if w:
                return w.geometry().bottom() + 2
        return pos.y()


# ── 任务列表视图 ────────────────────────────────────────────────────────
class TaskListView(QWidget):
    task_added        = Signal(str)
    task_completed    = Signal(int, bool)
    task_timer_toggled = Signal(int)
    task_deleted      = Signal(int)
    task_reordered    = Signal(list)   # List[int] — 新顺序的 task_id 列表
    task_edited       = Signal(int, str)  # task_id, new_title

    def __init__(self, parent=None):
        super().__init__(parent)
        self._task_widgets: dict[int, TaskItemWidget] = {}
        self._active_timer_id = None
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 4, 14, 8)
        layout.setSpacing(6)

        # 头部
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

        # 添加输入框
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

        # 滚动区域 — 使用 _TaskDropArea 作为内容容器
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setStyleSheet("background: transparent; border: none;")

        self.scroll_content = _TaskDropArea()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_layout.setSpacing(5)
        self.scroll_layout.addStretch(1)

        self.empty_label = QLabel("暂无待办事项，点击右上角添加 ✨")
        self.empty_label.setAlignment(Qt.AlignCenter)
        self.empty_label.setFont(QFont("Segoe UI Variable Display", 9))
        self.empty_label.setStyleSheet(f"color: {TEXT_MUTED_HEX}; padding: 20px 0;")
        self.scroll_layout.insertWidget(0, self.empty_label)

        self.scroll_content.item_dropped.connect(self._on_item_dropped)

        self.scroll.setWidget(self.scroll_content)
        layout.addWidget(self.scroll, 1)

    # ── 输入控制 ──────────────────────────────────────────────────────
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

    # ── 任务列表数据绑定 ──────────────────────────────────────────────
    def update_tasks(self, tasks: list):
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
        w.edit_requested.connect(self._on_item_edited)

        if self._active_timer_id == task.id:
            w.set_timer_active(True)

        self._task_widgets[task.id] = w
        self.scroll_layout.insertWidget(self.scroll_layout.count() - 1, w)

    def update_task_elapsed(self, task_id: int, elapsed: int):
        if task_id in self._task_widgets:
            self._task_widgets[task_id].set_elapsed(elapsed)

    def set_active_timer(self, task_id: int | None):
        self._active_timer_id = task_id
        for tid, w in self._task_widgets.items():
            w.set_timer_active(tid == task_id)

    # ── 条目事件槽 ────────────────────────────────────────────────────
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

    def _on_item_edited(self, task_id: int, new_title: str):
        self.task_edited.emit(task_id, new_title)

    def _on_item_dropped(self, task_id: int, target_idx: int):
        """拖拽放下后重排 layout 并通知上层。"""
        widget = self._task_widgets.get(task_id)
        if widget is None:
            return

        layout = self.scroll_layout

        # 找到当前 layout 位置
        source_idx = -1
        for i in range(layout.count()):
            item = layout.itemAt(i)
            if item and item.widget() is widget:
                source_idx = i
                break
        if source_idx < 0:
            return

        # 移除后下标需修正
        actual_target = target_idx if source_idx >= target_idx else target_idx - 1
        if source_idx == actual_target:
            return  # 位置未变

        layout.removeWidget(widget)
        layout.insertWidget(actual_target, widget)

        # 构建新顺序（逆向查找 widget → task_id）
        widget_to_id = {w: tid for tid, w in self._task_widgets.items()}
        new_order: list[int] = []
        for i in range(layout.count() - 1):   # 跳过末尾 stretch
            item = layout.itemAt(i)
            w = item.widget() if item else None
            if w and w in widget_to_id:
                new_order.append(widget_to_id[w])

        self.task_reordered.emit(new_order)

    # ── 统计 ─────────────────────────────────────────────────────────
    def update_stats(self, total: int, done: int):
        self.header_label.setText(f"TODAY  ({done}/{total})")

    def _update_header_stats(self, tasks: list):
        total = len(tasks)
        done = sum(1 for t in tasks if t.is_completed)
        self.update_stats(total, done)
