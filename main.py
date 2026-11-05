"""FloaTodo — pywebview 入口（HTML UI + Python 后端）
通信方式：
  Python→JS : window.evaluate_js()     [已验证可靠]
  JS→Python : HTTP fetch → cmd server  [最可靠，绕过 pywebview API bridge]
  JS→Python : window.pywebview.api.*   [备选]
"""
import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))

import webview

from core.clock        import ClockCore
from core.pomodoro     import PomodoroCore
from core.task_manager import TaskManager
from core.task_timer   import TaskTimer
from api               import FloaTodoAPI
import config.settings as settings_mod


def main() -> None:
    cfg = settings_mod.load()

    clock    = ClockCore()
    pomodoro = PomodoroCore()
    manager  = TaskManager()
    timer    = TaskTimer()

    pomodoro.configure(
        work       = cfg.get("pomodoro_work",      25),
        short      = cfg.get("pomodoro_short",      5),
        long       = cfg.get("pomodoro_long",      15),
        long_every = cfg.get("pomodoro_long_every",  4),
    )

    api = FloaTodoAPI(clock, pomodoro, manager, timer, cfg)

    # 启动 HTTP 命令服务器（JS fetch → Python）
    cmd_port = api.start_cmd_server()
    print(f"[FloaTodo] CMD server on port {cmd_port}")

    x = cfg.get("window_x", -1)
    y = cfg.get("window_y", -1)

    # 校验保存的位置：确保窗口（320×640）至少有 100×100 在屏幕内
    if x != -1 and y != -1:
        try:
            import ctypes as _ctypes
            sw = _ctypes.windll.user32.GetSystemMetrics(0)   # 屏幕宽
            sh = _ctypes.windll.user32.GetSystemMetrics(1)   # 屏幕高
            if x + 100 > sw or y + 100 > sh or x < -300 or y < 0:
                x, y = -1, -1  # 超出屏幕，重置为默认位置
        except Exception:
            pass

    html_path = Path(__file__).parent / "ui" / "index.html"

    win_kwargs = dict(
        title            = "FloaTodo",
        url              = str(html_path),
        js_api           = api,            # 保留 pywebview bridge 作为备选
        width            = 320,
        height           = 640,
        resizable        = False,
        frameless        = True,
        on_top           = True,
        min_size         = (1, 1),
        background_color = "#E8EAF0",
    )
    if x != -1 and y != -1:
        win_kwargs["x"] = x
        win_kwargs["y"] = y

    window = webview.create_window(**win_kwargs)
    api.set_window(window)

    # 页面加载完毕 → 注入 CMD_PORT 并触发 JS 初始化
    window.events.loaded += lambda: api.on_page_loaded()

    # 窗口关闭兜底
    window.events.closed += lambda: os._exit(0)

    webview.start(func=api.on_shown, debug=False, http_server=True)


if __name__ == "__main__":
    main()
