"""
FloaTodo Python-JS 桥接层
主要通道：本地 HTTP 命令服务器（JS fetch() → Python handler）
备选通道：pywebview API bridge（window.pywebview.api.*）
推送通道：evaluate_js（Python → JS，已验证可靠）
"""
from __future__ import annotations
import json
import threading
import http.server
import socketserver
import ctypes, ctypes.wintypes
from datetime import datetime
from typing import Optional

import config.settings as settings_mod

WEEKDAY_ZH = ["日", "一", "二", "三", "四", "五", "六"]


def _task_dict(task) -> dict:
    return {
        "id":      task.id,
        "title":   task.title,
        "done":    task.is_completed,
        "elapsed": task.elapsed_seconds,
    }


# ════════════════════════════════════════════════════════════════════════════
# 本地 HTTP 命令服务器（JS fetch → Python）
# 完全绕过 pywebview API bridge，直接走标准 HTTP 请求
# ════════════════════════════════════════════════════════════════════════════
class _CmdHandler(http.server.BaseHTTPRequestHandler):
    """处理来自 JS fetch() 的 POST 请求，分发到 FloaTodoAPI 方法。"""
    _api: "FloaTodoAPI | None" = None

    def do_OPTIONS(self):
        """CORS 预检请求"""
        self.send_response(200)
        self._cors()
        self.end_headers()

    def do_POST(self):
        try:
            n    = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(n).decode("utf-8"))
            method = body.get("method", "")
            args   = body.get("args", [])
        except Exception:
            self.send_response(400); self._cors(); self.end_headers()
            self.wfile.write(b'{"error":"bad request"}')
            return

        # 先发响应，再执行命令（防止 os._exit 中断 TCP 写入）
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self._cors()
        self.end_headers()
        self.wfile.write(b'{"ok":true}')

        # 在新线程中执行命令（100ms 后，让 JS fetch 先收到响应）
        def _run():
            import time; time.sleep(0.1)
            api = self.__class__._api
            if api and hasattr(api, method):
                try:
                    getattr(api, method)(*args)
                except Exception as e:
                    print(f"[CMD] {method} error: {e}")

        threading.Thread(target=_run, daemon=True).start()

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin",  "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def log_message(self, *_):
        pass  # 静默日志


class FloaTodoAPI:
    """pywebview js_api 类。"""

    def __init__(self, clock, pomodoro, manager, timer, cfg: dict):
        self._window   = None          # 由 main.py 在 start 后设置
        self._cfg      = cfg
        self.clock     = clock
        self.pomodoro  = pomodoro
        self.manager   = manager
        self.timer     = timer
        self._cmd_port : int = 0       # 本地 HTTP 命令服务器端口

        # 信号连接
        clock.time_ticked.connect(self._on_tick)
        pomodoro.tick.connect(self._on_pom_tick)
        pomodoro.phase_changed.connect(self._on_phase_changed)
        pomodoro.session_completed.connect(self._on_rounds)
        pomodoro.pomodoro_finished.connect(self._on_pomodoro_done)
        manager.task_added.connect(self._on_task_added)
        manager.task_deleted.connect(self._on_task_deleted)
        manager.task_updated.connect(self._on_task_updated)
        manager.task_completed.connect(self._on_task_updated)
        timer.elapsed_updated.connect(self._on_elapsed)

    def set_window(self, win) -> None:
        self._window = win

    # ── HTTP 命令服务器 ───────────────────────────────────────────────
    def start_cmd_server(self) -> int:
        """启动本地 HTTP 命令服务器，返回端口号。"""
        _CmdHandler._api = self
        srv = socketserver.TCPServer(("127.0.0.1", 0), _CmdHandler)
        self._cmd_port = srv.server_address[1]
        threading.Thread(target=srv.serve_forever, daemon=True,
                         name="cmd-server").start()
        return self._cmd_port

    def on_page_loaded(self) -> None:
        """页面加载完成 → 注入 CMD_PORT + 在此处查找 HWND（此时 <title> 已生效）。"""
        if self._cmd_port and self._window:
            self._js(f"window.CMD_PORT={self._cmd_port};initApp();")
        # 页面加载完成后 <title>FloaTodo</title> 已生效，FindWindowW 能找到正确 HWND
        threading.Thread(target=self._init_hwnd, daemon=True).start()

    # ── 向 JS 推送更新 ────────────────────────────────────────────────
    def _js(self, code: str) -> None:
        """线程安全地向 WebView 执行 JS。"""
        try:
            if self._window:
                self._window.evaluate_js(code)
        except Exception:
            pass

    def _on_tick(self, dt: datetime) -> None:
        h = dt.strftime("%H")
        m = dt.strftime("%M")
        s = dt.strftime("%S")
        date_str = f"周{WEEKDAY_ZH[dt.weekday()]}  {dt.year}年{dt.month}月{dt.day}日"
        self._js(f'window.app&&app.onTick("{h}:{m}:{s}","{date_str}")')
        # 驱动番茄钟和任务计时
        self.pomodoro.on_tick()
        self.timer.on_tick()

    def _on_pom_tick(self, remaining: int, total: int) -> None:
        self._js(f'window.app&&app.onPomTick({remaining},{total})')

    def _on_phase_changed(self, phase_value: str, duration: int) -> None:
        self._js(f'window.app&&app.onPhaseChanged("{phase_value}",{duration})')

    def _on_rounds(self, n: int) -> None:
        self._js(f'window.app&&app.onRounds({n})')

    def _on_pomodoro_done(self) -> None:
        self._js('window.app&&app.onPomDone()')

    def _on_task_added(self, task) -> None:
        self._js(f'window.app&&app.onTaskAdded({json.dumps(_task_dict(task))})')

    def _on_task_deleted(self, task_id: int) -> None:
        self._js(f'window.app&&app.onTaskDeleted({task_id})')

    def _on_task_updated(self, task) -> None:
        self._js(f'window.app&&app.onTaskUpdated({json.dumps(_task_dict(task))})')

    def _on_elapsed(self, task_id: int, elapsed: int) -> None:
        self._js(f'window.app&&app.onElapsed({task_id},{elapsed})')

    # ── 初始化 ──────────────────────────────────────────────────────────
    def getInitialState(self) -> str:
        return json.dumps({
            "tasks":  [_task_dict(t) for t in self.manager.tasks],
            "rounds": self.pomodoro.completed_rounds,
        })

    # ── 番茄钟 API ───────────────────────────────────────────────────
    def startPomodoro(self) -> None:
        self.pomodoro.start()

    def pausePomodoro(self) -> None:
        self.pomodoro.pause()

    def skipPhase(self) -> None:
        self.pomodoro.skip()

    def resetPomodoro(self) -> None:
        self.pomodoro.reset()

    def setPomodoroConfig(self, work: int, short_b: int, long_b: int) -> None:
        self.pomodoro.configure(int(work), int(short_b), int(long_b))

    # ── 任务 API ─────────────────────────────────────────────────────
    def addTask(self, title: str) -> int:
        task = self.manager.add_task(str(title))
        return task.id

    def deleteTask(self, task_id: int) -> bool:
        return self.manager.delete_task(int(task_id))

    def completeTask(self, task_id: int) -> None:
        self.manager.complete_task(int(task_id))

    def uncompleteTask(self, task_id: int) -> None:
        self.manager.uncomplete_task(int(task_id))

    # ── 任务计时 API ─────────────────────────────────────────────────
    def startTaskTimer(self, task_id: int) -> None:
        t = self.manager._find(int(task_id))
        if t:
            self.timer.start(int(task_id), t.elapsed_seconds)

    def stopTaskTimer(self, task_id: int) -> int:
        elapsed = self.timer.stop()
        self.manager.update_elapsed(int(task_id), elapsed)
        return elapsed

    # ── 窗口控制 API ─────────────────────────────────────────────────
    def moveWindow(self, dx: int, dy: int) -> None:
        """Win32 SetWindowPos 实现平滑拖拽（WebView2 不支持 CSS app-region）。"""
        try:
            hwnd = getattr(self, '_cached_hwnd', None) or self._find_hwnd()
            if not hwnd:
                return
            rect = ctypes.wintypes.RECT()
            ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rect))
            x = rect.left + int(dx)
            y = rect.top  + int(dy)
            SWP_NOSIZE     = 0x0001
            SWP_NOZORDER   = 0x0004
            SWP_NOACTIVATE = 0x0010
            ctypes.windll.user32.SetWindowPos(
                hwnd, None, x, y, 0, 0,
                SWP_NOSIZE | SWP_NOZORDER | SWP_NOACTIVATE
            )
        except Exception:
            pass

    def resizeWindow(self, w: int, h: int) -> None:
        """调整窗口大小：同时用 pywebview 内置 resize 和 Win32 SetWindowPos，
        双管齐下确保生效。"""
        W, H = int(w), int(h)
        # 1. pywebview 内置 resize（总是尝试）
        try:
            self._window.resize(W, H)
        except Exception:
            pass
        # 2. Win32 SetWindowPos（如果有 HWND 则额外保证）
        hwnd = getattr(self, '_cached_hwnd', None) or self._find_hwnd()
        if hwnd:
            try:
                SWP_NOMOVE     = 0x0002
                SWP_NOZORDER   = 0x0004
                SWP_NOACTIVATE = 0x0010
                ctypes.windll.user32.SetWindowPos(
                    hwnd, None, 0, 0, W, H,
                    SWP_NOMOVE | SWP_NOZORDER | SWP_NOACTIVATE
                )
            except Exception:
                pass
        # 重新应用圆角（延迟执行等 resize 完成）
        threading.Timer(0.25, self._apply_round_corners).start()

    def minimizeWindow(self) -> None:
        """最小化到任务栏。优先用 Win32 ShowWindow（需 HWND），fallback pywebview。"""
        hwnd = getattr(self, '_cached_hwnd', None)
        if hwnd:
            try:
                # WM_SYSCOMMAND SC_MINIMIZE：最标准的 Windows 最小化方式
                ctypes.windll.user32.PostMessageW(hwnd, 0x0112, 0xF020, 0)
                return
            except Exception:
                pass
        # Fallback：pywebview 内置 minimize
        try:
            self._window.minimize()
        except Exception:
            pass

    def restoreWindow(self) -> None:
        """恢复隐藏的窗口（供全局热键调用）。"""
        try:
            self._window.show()
        except Exception:
            pass
        # 确保置顶
        try:
            hwnd = getattr(self, '_cached_hwnd', None) or self._find_hwnd()
            if hwnd:
                HWND_TOPMOST = -1
                SWP_NOMOVE = 0x0002; SWP_NOSIZE = 0x0001
                ctypes.windll.user32.SetWindowPos(
                    hwnd, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE)
                ctypes.windll.user32.SetForegroundWindow(hwnd)
        except Exception:
            pass

    def closeWindow(self) -> None:
        """关闭应用。
        注意：迷你模式（窗口宽≤200px）下不保存坐标，避免下次启动窗口超出屏幕。
        """
        self.clock.stop()
        try:
            hwnd = getattr(self, '_cached_hwnd', None) or self._find_hwnd()
            if hwnd:
                rect = ctypes.wintypes.RECT()
                ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rect))
                win_w = rect.right - rect.left
                # 仅在完整模式（宽>200px）时保存位置；迷你模式位置会让全窗口超出屏幕
                if win_w > 200:
                    self._cfg["window_x"] = rect.left
                    self._cfg["window_y"] = rect.top
                else:
                    # 迷你模式：重置为默认位置（下次启动在屏幕右下角）
                    self._cfg["window_x"] = -1
                    self._cfg["window_y"] = -1
        except Exception:
            pass
        try:
            settings_mod.save(self._cfg)
        except Exception:
            pass
        import os
        os._exit(0)

    def savePosition(self, x: int, y: int) -> None:
        self._cfg["window_x"] = int(x)
        self._cfg["window_y"] = int(y)

    # ── 窗口初始化回调（由 webview.start(func=...) 调用）────────────
    def on_shown(self) -> None:
        """pywebview 窗口显示后调用：启动时钟，注册热键。
        HWND 查找移到 on_page_loaded（页面加载完才有正确标题）。"""
        self.clock.start()
        threading.Thread(target=self._register_hotkey, daemon=True).start()

    def _register_hotkey(self) -> None:
        try:
            import keyboard
            keyboard.add_hotkey('ctrl+shift+f', self.restoreWindow, suppress=False)
        except Exception:
            pass

    def _init_hwnd(self) -> None:
        """查找并缓存本窗口 HWND，然后应用圆角。
        移到 on_page_loaded 中调用，此时 <title>FloaTodo</title> 已生效。"""
        import time

        for _ in range(30):   # 最多重试 3s（每次 100ms）
            hwnd = self._locate_hwnd()
            if hwnd:
                self._cached_hwnd = hwnd
                self._apply_round_corners()
                return
            time.sleep(0.1)

        # 未找到 HWND —— 仍尝试应用圆角（会走 fallback 路径）
        self._apply_round_corners()

    def _locate_hwnd(self) -> int:
        """尝试多种方式定位本窗口 HWND。"""
        # 方法 1：FindWindowW 按标题（页面加载后 <title> 生效）
        hwnd = ctypes.windll.user32.FindWindowW(None, "FloaTodo")
        if hwnd and ctypes.windll.user32.IsWindowVisible(hwnd):
            return hwnd

        # 方法 2：前台窗口
        fg = ctypes.windll.user32.GetForegroundWindow()
        if fg:
            buf = ctypes.create_unicode_buffer(256)
            ctypes.windll.user32.GetWindowTextW(fg, buf, 256)
            if "FloaTodo" in buf.value:
                return fg

        # 方法 3：EnumWindows —— 按标题
        hwnd = self._find_hwnd()
        if hwnd:
            return hwnd

        # 方法 4：EnumWindows —— 按尺寸（320×640±50，作为最后手段）
        result = [0]
        @ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)
        def size_cb(h, _):
            if ctypes.windll.user32.IsWindowVisible(h):
                r = ctypes.wintypes.RECT()
                ctypes.windll.user32.GetWindowRect(h, ctypes.byref(r))
                w, hh = r.right - r.left, r.bottom - r.top
                if 270 <= w <= 370 and 500 <= hh <= 750:
                    # 检查是 POPUP 且 TOPMOST（我们的窗口特征）
                    ex = ctypes.windll.user32.GetWindowLongW(h, -20)
                    if ex & 0x8:    # WS_EX_TOPMOST
                        result[0] = h
                        return False
            return True
        ctypes.windll.user32.EnumWindows(size_cb, 0)
        return result[0]

    # ── Win32 圆角 ──────────────────────────────────────────────────
    def _apply_round_corners(self, radius: int = 20) -> None:
        try:
            hwnd = getattr(self, '_cached_hwnd', None) or self._find_hwnd()
            if not hwnd:
                return
            rect = ctypes.wintypes.RECT()
            ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rect))
            w = rect.right  - rect.left
            h = rect.bottom - rect.top
            # 迷你模式（宽≤140）用更大圆角，接近圆形
            r = radius * 2 if w <= 140 else radius
            hrgn = ctypes.windll.gdi32.CreateRoundRectRgn(0, 0, w + 1, h + 1, r, r)
            ctypes.windll.user32.SetWindowRgn(hwnd, hrgn, True)
        except Exception:
            pass

    def _find_hwnd(self) -> Optional[int]:
        result = [None]

        @ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)
        def cb(hwnd, _):
            if ctypes.windll.user32.IsWindowVisible(hwnd):
                buf = ctypes.create_unicode_buffer(256)
                ctypes.windll.user32.GetWindowTextW(hwnd, buf, 256)
                if "FloaTodo" in buf.value:
                    result[0] = hwnd
                    return False
            return True

        ctypes.windll.user32.EnumWindows(cb, 0)
        return result[0]
