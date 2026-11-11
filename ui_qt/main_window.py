"""
FloaTodo — 原生 Neumorphic 主窗体
融合 Windows 专注风格、统一纯色矢量控制键、番茄数统计、偏好设置面板与全阶段恒定宽度（374px）
纯净圆角硬件抗锯齿卡片渲染，彻底去除模糊阴影边缘截断导致的底部灰斑与分层条纹
"""
import sys
from pathlib import Path
from datetime import datetime
from PySide6.QtCore import Qt, QTimer, QPoint, QObject, QEvent
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QSystemTrayIcon, QMenu, QApplication
)
from PySide6.QtGui import QFont, QIcon, QPixmap, QPainter, QColor, QAction, QMouseEvent, QCursor

from core.pomodoro import PomodoroCore
from core.task_manager import TaskManager
from core.task_timer import TaskTimer
from core.models import PomodoroPhase
import config.settings as settings_mod

from ui_qt.styles import (
    BG_HEX, BG_PRESSED_HEX, TEXT_PRI_HEX, TEXT_SEC_HEX, TEXT_MUTED_HEX,
    ACCENT_WORK, MAIN_QSS
)
from ui_qt.title_bar import TitleBar
from ui_qt.focus_dial import FocusDial
from ui_qt.task_widget import TaskListView
from ui_qt.controls import RoundIconButton, IconType
from ui_qt.settings_dialog import SettingsDialog
from ui_qt.sound_manager import get_sound_manager
from ui_qt.window_effects import enable_glass, disable_glass

WEEKDAY_ZH = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]

# ── 边缘拖拽缩放（纯 Qt 实现，无 Win32 ctypes）────────────────────────
# 通过应用级事件过滤器检测窗口边缘，调用 QWindow.startSystemResize()
# 由操作系统原生处理拖拽，自动遵守 setMinimumSize / setMaximumSize 约束
_RESIZE_BORDER = 7  # px

_EDGE_CURSORS = {
    Qt.Edge.LeftEdge:                                   Qt.CursorShape.SizeHorCursor,
    Qt.Edge.RightEdge:                                  Qt.CursorShape.SizeHorCursor,
    Qt.Edge.TopEdge:                                    Qt.CursorShape.SizeVerCursor,
    Qt.Edge.BottomEdge:                                 Qt.CursorShape.SizeVerCursor,
    Qt.Edge.LeftEdge  | Qt.Edge.TopEdge:                Qt.CursorShape.SizeFDiagCursor,
    Qt.Edge.RightEdge | Qt.Edge.BottomEdge:             Qt.CursorShape.SizeFDiagCursor,
    Qt.Edge.RightEdge | Qt.Edge.TopEdge:                Qt.CursorShape.SizeBDiagCursor,
    Qt.Edge.LeftEdge  | Qt.Edge.BottomEdge:             Qt.CursorShape.SizeBDiagCursor,
}


class _ResizeFilter(QObject):
    """应用级事件过滤器：在窗口边缘实现拖拽缩放。
    通过 QWindow.startSystemResize() 委托 OS 执行原生缩放，
    无需 ctypes 转换 Win32 消息结构，不干扰 Qt 鼠标事件路由。"""

    def __init__(self, win: "MainWindow"):
        super().__init__(win)
        self._win = win
        self._cursor_overridden = False

    def _edges_at(self, gpos: QPoint) -> Qt.Edge:
        if self._win._is_mini:
            return Qt.Edge(0)
        r = self._win.frameGeometry()
        lx = gpos.x() - r.x()
        ly = gpos.y() - r.y()
        w, h = r.width(), r.height()
        b = _RESIZE_BORDER
        e = Qt.Edge(0)
        if lx < b:     e |= Qt.Edge.LeftEdge
        if lx > w - b: e |= Qt.Edge.RightEdge
        if ly < b:     e |= Qt.Edge.TopEdge
        if ly > h - b: e |= Qt.Edge.BottomEdge
        return e

    def eventFilter(self, obj, event) -> bool:
        if not isinstance(event, QMouseEvent):
            return False

        gpos = event.globalPosition().toPoint()
        edges = self._edges_at(gpos)

        if event.type() == QEvent.Type.MouseButtonPress:
            if event.button() == Qt.MouseButton.LeftButton and edges:
                handle = self._win.windowHandle()
                if handle:
                    handle.startSystemResize(edges)
                return True   # 吃掉此事件，交给 OS 处理

        elif event.type() == QEvent.Type.MouseMove:
            if edges:
                cursor = _EDGE_CURSORS.get(edges, Qt.CursorShape.SizeAllCursor)
                QApplication.setOverrideCursor(cursor)
                self._cursor_overridden = True
            elif self._cursor_overridden:
                QApplication.restoreOverrideCursor()
                self._cursor_overridden = False

        return False


def make_app_icon() -> QIcon:
    if getattr(sys, "frozen", False):
        app_root = Path(sys.executable).parent
    else:
        app_root = Path(__file__).parent.parent
    ico_path = app_root / "app.ico"
    if ico_path.exists():
        return QIcon(str(ico_path))
    if hasattr(sys, "_MEIPASS"):
        meipass_ico = Path(sys._MEIPASS) / "app.ico"
        if meipass_ico.exists():
            return QIcon(str(meipass_ico))
    pix = QPixmap(32, 32)
    pix.fill(Qt.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.Antialiasing)
    p.setFont(QFont("Segoe UI Emoji", 20))
    p.drawText(pix.rect(), Qt.AlignCenter, "🍅")
    p.end()
    return QIcon(pix)


class MainWindow(QMainWindow):
    def __init__(self, cfg: dict):
        super().__init__()
        self.cfg = cfg
        self.total_tomatoes: int = int(cfg.get("total_tomatoes", 0))
        self.sound_mgr = get_sound_manager()

        # 核心业务对象
        self.pomodoro = PomodoroCore()
        self.task_mgr = TaskManager()
        self.task_timer = TaskTimer()

        self.pomodoro.configure(
            work=cfg.get("pomodoro_work", 25),
            short=cfg.get("pomodoro_short", 5),
            long=cfg.get("pomodoro_long", 15),
            long_every=cfg.get("pomodoro_long_every", 4),
        )

        self._is_mini = False
        self._glass_on = False          # 毛玻璃皮肤状态
        # 标准窗体尺寸（无软件截断投影，卡片全幅铺满）
        self._normal_size = (374, 660)
        self._mini_size = (148, 185)
        # 缩放参数：维持 374:660 长宽比，最小 1×，最大 2×
        self._aspect = 660 / 374        # ≈ 1.765
        self._min_w = 374
        self._max_w = 748

        # 基础窗口属性
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowSystemMenuHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setStyleSheet(MAIN_QSS)
        self.setWindowTitle("FloaTodo")
        self.setWindowIcon(make_app_icon())

        if self.cfg.get("always_on_top", True):
            self.setWindowFlag(Qt.WindowStaysOnTopHint, True)

        self._init_ui()
        self._init_tray()
        self._connect_signals()
        self._init_timer()
        self._restore_position()

        # 安装应用级边缘缩放过滤器（纯 Qt，不干扰鼠标事件路由）
        self._resize_filter = _ResizeFilter(self)
        QApplication.instance().installEventFilter(self._resize_filter)

    def _init_ui(self):
        self.root_widget = QWidget(self)
        self.setCentralWidget(self.root_widget)

        # 边距完全归零，消除任何外部半透阴影被切断产生的底部灰斑分层
        self.root_layout = QVBoxLayout(self.root_widget)
        self.root_layout.setContentsMargins(0, 0, 0, 0)

        self.card = QFrame(self.root_widget)
        self.card.setObjectName("mainCard")
        self.card.setStyleSheet(f"""
            QFrame#mainCard {{
                background-color: {BG_HEX};
                border-radius: 18px;
                border: 1px solid rgba(174, 174, 192, 0.42);
            }}
        """)

        self.card_layout = QVBoxLayout(self.card)
        self.card_layout.setContentsMargins(0, 0, 0, 8)
        self.card_layout.setSpacing(0)

        # 1. 自定义标题栏
        self.title_bar = TitleBar(self)
        self.card_layout.addWidget(self.title_bar)

        # 2. 专注展示核心区域
        self.focus_container = QWidget()
        focus_layout = QVBoxLayout(self.focus_container)
        focus_layout.setContentsMargins(8, 0, 8, 4)
        focus_layout.setSpacing(4)
        focus_layout.setAlignment(Qt.AlignCenter)

        # 刻度表盘
        self.dial = FocusDial(self)
        self.dial.clicked.connect(self._toggle_pomodoro)
        focus_layout.addWidget(self.dial, 0, Qt.AlignCenter)

        # 控制操作区：布局为 [ >> 下一阶段 ] [ 开始/暂停 (大中) ] [ ··· 更多 ]
        self.ctrl_container = QWidget()
        self.ctrl_layout = QHBoxLayout(self.ctrl_container)
        self.ctrl_layout.setContentsMargins(0, 2, 0, 4)
        self.ctrl_layout.setSpacing(14)
        self.ctrl_layout.setAlignment(Qt.AlignCenter)

        # 左侧：跳过/下一阶段键 (>>)
        self.btn_skip = RoundIconButton(IconType.SKIP, size=38, is_accent=False, parent=self.ctrl_container)
        self.btn_skip.setToolTip("跳过当前阶段进入下一阶段")
        self.btn_skip.clicked.connect(self._skip_pomodoro)
        self.ctrl_layout.addWidget(self.btn_skip)

        # 中间：播放/暂停主按键（52px 大圆）
        self.btn_play = RoundIconButton(IconType.PLAY, size=52, is_accent=False, parent=self.ctrl_container)
        self.btn_play.setToolTip("开始专注 / 暂停")
        self.btn_play.clicked.connect(self._toggle_pomodoro)
        self.ctrl_layout.addWidget(self.btn_play)

        # 右侧：更多菜单键 (···)
        self.btn_more = RoundIconButton(IconType.MORE, size=38, is_accent=False, parent=self.ctrl_container)
        self.btn_more.setToolTip("设置与选项")
        self.btn_more.clicked.connect(self._show_pomodoro_menu)
        self.ctrl_layout.addWidget(self.btn_more)

        focus_layout.addWidget(self.ctrl_container)

        # 下一阶段提示文本
        self.label_next_stage = QLabel("下一个: 5 分钟休息")
        self.label_next_stage.setAlignment(Qt.AlignCenter)
        self.label_next_stage.setFont(QFont("Segoe UI Variable Display", 9))
        self.label_next_stage.setStyleSheet(f"color: {TEXT_SEC_HEX};")
        focus_layout.addWidget(self.label_next_stage)

        self.card_layout.addWidget(self.focus_container)

        # 分割线
        self.divider = QFrame()
        self.divider.setFixedHeight(1)
        self.divider.setStyleSheet("background-color: rgba(174, 174, 192, 0.35); margin: 6px 14px;")
        self.card_layout.addWidget(self.divider)

        # 3. 待办任务列表区域
        self.task_list_view = TaskListView(self)
        self.card_layout.addWidget(self.task_list_view, 1)

        self.root_layout.addWidget(self.card)

        # 允许拖拽缩放（由 _ResizeFilter + startSystemResize 实现）
        self.setMinimumSize(self._min_w, int(self._min_w * self._aspect))
        self.setMaximumSize(self._max_w, int(self._max_w * self._aspect))
        self.resize(*self._normal_size)

    def _update_play_btn_style(self, running: bool):
        if running:
            self.btn_play.set_icon_type(IconType.PAUSE, is_accent=True)
        else:
            self.btn_play.set_icon_type(IconType.PLAY, is_accent=False)

    def _init_tray(self):
        self.tray = QSystemTrayIcon(make_app_icon(), self)
        self.tray.setToolTip("FloaTodo — 专注悬浮待办")

        menu = QMenu()
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {BG_HEX};
                border-radius: 8px;
                padding: 4px;
                border: 1px solid rgba(174, 174, 192, 0.3);
            }}
            QMenu::item {{
                padding: 6px 18px;
                border-radius: 5px;
                font-size: 12px;
                color: {TEXT_PRI_HEX};
            }}
            QMenu::item:selected {{
                background-color: {BG_PRESSED_HEX};
            }}
        """)
        show_action = QAction("显示/隐藏窗口", menu)
        show_action.triggered.connect(self._toggle_window_visibility)
        menu.addAction(show_action)

        settings_action = QAction("偏好设置...", menu)
        settings_action.triggered.connect(self._open_settings_dialog)
        menu.addAction(settings_action)

        menu.addSeparator()
        quit_action = QAction("退出应用", menu)
        quit_action.triggered.connect(self.close)
        menu.addAction(quit_action)

        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._on_tray_activated)
        self.tray.show()

    def _connect_signals(self):
        self.title_bar.pin_toggled.connect(self._set_always_on_top)
        self.title_bar.mini_clicked.connect(self._toggle_mini_mode)
        self.title_bar.frost_clicked.connect(self._toggle_glass)
        self.title_bar.minimize_clicked.connect(self.showMinimized)
        self.title_bar.close_clicked.connect(self.close)

        self.pomodoro.tick.connect(self._on_pom_tick)
        self.pomodoro.phase_changed.connect(self._on_pom_phase_changed)
        self.pomodoro.session_completed.connect(self._on_pom_session_completed)
        self.pomodoro.cycle_completed.connect(self._on_cycle_completed)
        self.pomodoro.pomodoro_finished.connect(self._on_pom_finished)

        self.task_list_view.task_added.connect(self._add_task)
        self.task_list_view.task_completed.connect(self._complete_task)
        self.task_list_view.task_timer_toggled.connect(self._toggle_task_timer)
        self.task_list_view.task_deleted.connect(self._delete_task)

        self.task_timer.elapsed_updated.connect(self.task_list_view.update_task_elapsed)

        self.task_list_view.update_tasks(self.task_mgr.tasks)
        self.dial.set_phase("idle", self.pomodoro.total)
        self.dial.set_tick(self.pomodoro.total, self.pomodoro.total)
        self._update_stage_title()

    def _init_timer(self):
        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self._on_heartbeat)
        self.timer.start()

    def _on_heartbeat(self):
        self.pomodoro.on_tick()
        self.task_timer.on_tick()
        # 迷你模式 + IDLE 时，表盘中心显示实时时钟（HH:MM）
        if self._is_mini and self.pomodoro.phase.value == "idle":
            from datetime import datetime
            self.dial.set_clock_text(datetime.now().strftime("%H:%M"))
        else:
            self.dial.set_clock_text("")   # 非迷你或有番茄在跑时不显示时钟

    # ── 番茄钟控制 ─────────────────────────────────────────────────────
    def _toggle_pomodoro(self):
        if self.pomodoro.is_running:
            self.pomodoro.pause()
            self.dial.set_running(False)
            self._update_play_btn_style(False)
        else:
            self.pomodoro.start()
            self.dial.set_running(True)
            self._update_play_btn_style(True)
        self._update_stage_title()

    def _skip_pomodoro(self):
        self.pomodoro.skip()
        self.dial.set_phase(self.pomodoro.phase.value, self.pomodoro.total)
        self.dial.set_tick(self.pomodoro.remaining, self.pomodoro.total)
        self.dial.set_running(self.pomodoro.is_running)
        self._update_play_btn_style(self.pomodoro.is_running)
        self._update_stage_title()

    def _show_pomodoro_menu(self):
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
            QMenu::item:disabled {{
                color: {ACCENT_WORK};
                font-weight: bold;
            }}
        """)

        # 1. 战利品番茄数统计项
        stat_action = QAction(f"🍅 × {self.total_tomatoes}", menu)
        stat_action.setEnabled(False)
        menu.addAction(stat_action)

        menu.addSeparator()

        # 2. 偏好设置按钮
        settings_action = QAction("⚙️ 偏好设置...", menu)
        settings_action.triggered.connect(self._open_settings_dialog)
        menu.addAction(settings_action)

        # 3. 重置当前阶段与轮数
        reset_action = QAction("🔄 重置当前阶段与轮数", menu)
        reset_action.triggered.connect(self._reset_pomodoro)
        menu.addAction(reset_action)

        # 4. 番茄数清空
        clear_action = QAction("🗑 番茄数清空", menu)
        clear_action.triggered.connect(self._clear_tomatoes)
        menu.addAction(clear_action)

        menu.exec(self.btn_more.mapToGlobal(QPoint(0, self.btn_more.height() + 4)))

    def _open_settings_dialog(self):
        dlg = SettingsDialog(self.cfg, self)
        dlg.settings_saved.connect(self._on_settings_applied)
        dlg.exec()

    def _on_settings_applied(self, new_cfg: dict):
        self.cfg = new_cfg
        try:
            settings_mod.save(self.cfg)
        except Exception:
            pass

        self.pomodoro.configure(
            work=self.cfg.get("pomodoro_work", 25),
            short=self.cfg.get("pomodoro_short", 5),
            long=self.cfg.get("pomodoro_long", 15),
            long_every=self.cfg.get("pomodoro_long_every", 4),
        )

        if self.pomodoro.phase == PomodoroPhase.IDLE:
            self.dial.set_phase("idle", self.pomodoro.total)
            self.dial.set_tick(self.pomodoro.total, self.pomodoro.total)

        self._update_stage_title()

    def _on_cycle_completed(self):
        self.total_tomatoes += 1
        self.cfg["total_tomatoes"] = self.total_tomatoes
        try:
            settings_mod.save(self.cfg)
        except Exception:
            pass
        self._update_stage_title()

        self.sound_mgr.play("done", self.cfg)

        self.tray.showMessage(
            "🍅 达成大满贯！收获番茄",
            f"太棒了！已完成完整专注，收获 1 个大番茄！当前累计：🍅 × {self.total_tomatoes}",
            QSystemTrayIcon.Information,
            5000
        )

    def _clear_tomatoes(self):
        self.total_tomatoes = 0
        self.cfg["total_tomatoes"] = 0
        try:
            settings_mod.save(self.cfg)
        except Exception:
            pass
        self._update_stage_title()

    def _reset_pomodoro(self):
        self.pomodoro.reset()
        self.dial.set_phase("idle", self.pomodoro.total)
        self.dial.set_tick(self.pomodoro.total, self.pomodoro.total)
        self.dial.set_running(False)
        self._update_play_btn_style(False)
        self._update_stage_title()

    def _on_pom_tick(self, remaining: int, total: int):
        self.dial.set_tick(remaining, total)

    def _on_pom_phase_changed(self, phase: str, duration: int):
        self.dial.set_phase(phase, duration)
        self.dial.set_tick(duration, duration)
        self._update_play_btn_style(self.pomodoro.is_running)
        self._update_stage_title()
        self._notify_phase_change(phase)

    def _on_pom_session_completed(self, rounds: int):
        self._update_stage_title()

    def _on_pom_finished(self):
        self.dial.trigger_completion_ripple()

    def _notify_phase_change(self, phase: str):
        sound_type = "done" if phase == "long" else "next"
        self.sound_mgr.play(sound_type, self.cfg)

        self.dial.trigger_completion_ripple()
        QApplication.alert(self, 3000)

        if phase == "work":
            title = "🍅 专注时间开始！"
            msg = "开始一段专注高效的工作吧，加油！"
        elif phase == "short":
            title = "☕ 专注完成，休息一下！"
            msg = "恭喜完成一个专注段！休息放松一下肩膀~"
        elif phase == "long":
            title = "🌿 恭喜完成一整轮专注！"
            msg = "太棒了！休息好好恢复精力吧~"
        else:
            return

        self.tray.showMessage(title, msg, QSystemTrayIcon.Information, 4500)

    def _update_stage_title(self):
        phase = self.pomodoro.phase
        rounds = self.pomodoro.completed_rounds
        long_every = self.pomodoro._session.long_break_every

        current_round_idx = (rounds % long_every) + 1
        if phase == PomodoroPhase.WORK:
            title = f"专注时间段 (第 {current_round_idx} 个/共 {long_every} 个)"
            if current_round_idx == long_every:
                next_str = f"下一个: {self.pomodoro._session.long_duration // 60} 分钟长休"
            else:
                next_str = f"下一个: {self.pomodoro._session.short_duration // 60} 分钟休息"
        elif phase == PomodoroPhase.SHORT_BREAK:
            title = f"短休时间段 ☕ (第 {current_round_idx - 1 if current_round_idx > 1 else long_every} 轮完成)"
            next_str = f"下一个: {self.pomodoro._session.work_duration // 60} 分钟专注"
        elif phase == PomodoroPhase.LONG_BREAK:
            title = f"长休时间段 🌿 (第 {long_every} 轮满贯达成)"
            next_str = f"下一个: {self.pomodoro._session.work_duration // 60} 分钟专注"
        else:
            title = f"专注时间段 (第 {current_round_idx} 个/共 {long_every} 个)"
            next_str = f"下一个: {self.pomodoro._session.short_duration // 60} 分钟休息"

        self.title_bar.set_stage_text(title)

        tomatoes_tag = f"  •  🍅 × {self.total_tomatoes}" if self.total_tomatoes > 0 else ""
        self.label_next_stage.setText(f"{next_str}{tomatoes_tag}")

    # ── 任务管理操作 ───────────────────────────────────────────────────
    def _add_task(self, title: str):
        task = self.task_mgr.add_task(title)
        self.task_list_view.add_task_item(task)
        self.task_list_view._update_header_stats(self.task_mgr.tasks)

    def _complete_task(self, task_id: int, done: bool):
        if done:
            self.task_mgr.complete_task(task_id)
        else:
            self.task_mgr.uncomplete_task(task_id)
        self.task_list_view._update_header_stats(self.task_mgr.tasks)

    def _delete_task(self, task_id: int):
        self.task_mgr.delete_task(task_id)
        self.task_list_view._update_header_stats(self.task_mgr.tasks)

    def _toggle_task_timer(self, task_id: int):
        if self.task_timer.active_task_id == task_id:
            elapsed = self.task_timer.stop()
            self.task_mgr.update_elapsed(task_id, elapsed)
            self.task_list_view.set_active_timer(None)
        else:
            if self.task_timer.active_task_id is not None:
                prev_id = self.task_timer.active_task_id
                prev_elapsed = self.task_timer.stop()
                self.task_mgr.update_elapsed(prev_id, prev_elapsed)

            task = self.task_mgr._find(task_id)
            if task:
                self.task_timer.start(task_id, task.elapsed_seconds)
                self.task_list_view.set_active_timer(task_id)

    # ── 窗口状态与迷你模式 ──────────────────────────────────────────────
    def _set_always_on_top(self, on_top: bool):
        self.cfg["always_on_top"] = on_top
        self.setWindowFlag(Qt.WindowStaysOnTopHint, on_top)
        self.show()

    def _toggle_mini_mode(self):
        self._is_mini = not self._is_mini
        self.title_bar.set_mini_mode(self._is_mini)

        if self._is_mini:
            self.btn_skip.hide()
            self.btn_more.hide()
            self.label_next_stage.hide()
            self.divider.hide()
            self.task_list_view.hide()

            self.root_layout.setContentsMargins(0, 0, 0, 0)
            self.card_layout.setContentsMargins(0, 0, 0, 4)
            self.card.setStyleSheet(f"""
                QFrame#mainCard {{
                    background-color: {BG_HEX};
                    border-radius: 14px;
                    border: 1px solid rgba(174, 174, 192, 0.42);
                }}
            """)

            self.dial.setFixedSize(110, 110)
            self.btn_play.setFixedSize(36, 36)

            self.setFixedSize(self._mini_size[0], self._mini_size[1])
        else:
            self.btn_skip.show()
            self.btn_more.show()
            self.label_next_stage.show()
            self.divider.show()
            self.task_list_view.show()

            self.root_layout.setContentsMargins(0, 0, 0, 0)
            self.card_layout.setContentsMargins(0, 0, 0, 8)
            self.card.setStyleSheet(f"""
                QFrame#mainCard {{
                    background-color: {BG_HEX};
                    border-radius: 18px;
                    border: 1px solid rgba(174, 174, 192, 0.42);
                }}
            """)

            # 先解除迷你模式的 setFixedSize 锁定，再设正常约束
            # （setFixedSize 会把 min=max 锁死，必须先解除，否则 resize 无效）
            self.dial.setMinimumSize(0, 0)
            self.dial.setMaximumSize(16777215, 16777215)
            self.dial.setMinimumSize(180, 180)
            self.dial.setMaximumSize(320, 320)
            self.dial.resize(240, 240)
            self.btn_play.setFixedSize(52, 52)

            # 窗口同理：先解除 min/max 锁，再设正常范围
            self.setMinimumSize(0, 0)
            self.setMaximumSize(16777215, 16777215)
            self.setMinimumSize(self._min_w, int(self._min_w * self._aspect))
            self.setMaximumSize(self._max_w, int(self._max_w * self._aspect))
            self.resize(*self._normal_size)

    # ── 毛玻璃皮肤 ─────────────────────────────────────────────────────
    def _toggle_glass(self):
        self._glass_on = not self._glass_on
        hwnd = int(self.winId())
        if self._glass_on:
            enable_glass(hwnd)
            # 卡片改为半透明玻璃样式
            self.card.setStyleSheet("""
                QFrame#mainCard {
                    background-color: rgba(235, 240, 255, 145);
                    border-radius: 18px;
                    border: 1px solid rgba(255, 255, 255, 180);
                }
            """)
        else:
            disable_glass(hwnd)
            self.card.setStyleSheet(f"""
                QFrame#mainCard {{
                    background-color: {BG_HEX};
                    border-radius: 18px;
                    border: 1px solid rgba(174, 174, 192, 0.42);
                }}
            """)
        self.title_bar.set_frost_active(self._glass_on)

    def _toggle_window_visibility(self):
        if self.isVisible():
            self.hide()
        else:
            self.showNormal()
            self.activateWindow()

    def _on_tray_activated(self, reason):
        if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick):
            self._toggle_window_visibility()

    def _restore_position(self):
        x = self.cfg.get("window_x", -1)
        y = self.cfg.get("window_y", -1)
        if x != -1 and y != -1:
            screen_geo = QApplication.primaryScreen().geometry()
            if 0 <= x <= screen_geo.width() - 80 and 0 <= y <= screen_geo.height() - 80:
                self.move(x, y)

    def closeEvent(self, event):
        if not self._is_mini:
            pos = self.pos()
            self.cfg["window_x"] = pos.x()
            self.cfg["window_y"] = pos.y()
        self.cfg["total_tomatoes"] = self.total_tomatoes
        try:
            settings_mod.save(self.cfg)
        except Exception:
            pass
        self.tray.hide()
        event.accept()
