"""FloaTodo — 应用主入口
默认启动原生 PySide6 界面（融合 Windows 专注风格表盘、原生抗锯齿渲染与无延迟拖动）。
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ── conda 环境 DLL 路径修复 ──────────────────────────────────────────
# conda 编译的 PySide6 依赖 <conda_root>/Library/bin 里的 Qt DLL。
# IDE / 双击启动时 conda activate 未运行，需手动加入搜索路径。
def _ensure_conda_dll_path() -> None:
    conda_root = os.path.dirname(sys.executable)   # e.g. D:\Anaconda
    lib_bin = os.path.join(conda_root, "Library", "bin")
    if os.path.isdir(lib_bin):
        # add_dll_directory（Python 3.8+）：比 PATH 更可靠的 DLL 搜索路径
        try:
            os.add_dll_directory(lib_bin)
        except Exception:
            pass
        # 同时更新 PATH，保证 Qt 插件/平台驱动能找到依赖
        current = os.environ.get("PATH", "")
        if lib_bin.lower() not in current.lower():
            os.environ["PATH"] = lib_bin + os.pathsep + current

_ensure_conda_dll_path()


def run_qt():
    from main_qt import main as qt_main
    qt_main()


def run_webview():
    from pathlib import Path
    import webview
    from core.clock import ClockCore
    from core.pomodoro import PomodoroCore
    from core.task_manager import TaskManager
    from core.task_timer import TaskTimer
    from api import FloaTodoAPI
    import config.settings as settings_mod

    cfg = settings_mod.load()
    clock = ClockCore()
    pomodoro = PomodoroCore()
    manager = TaskManager()
    timer = TaskTimer()

    pomodoro.configure(
        work=cfg.get("pomodoro_work", 25),
        short=cfg.get("pomodoro_short", 5),
        long=cfg.get("pomodoro_long", 15),
        long_every=cfg.get("pomodoro_long_every", 4),
    )

    api = FloaTodoAPI(clock, pomodoro, manager, timer, cfg)
    cmd_port = api.start_cmd_server()
    print(f"[FloaTodo] Webview CMD server on port {cmd_port}")

    html_path = Path(__file__).parent / "ui" / "index.html"
    window = webview.create_window(
        title="FloaTodo",
        url=str(html_path),
        js_api=api,
        width=320,
        height=640,
        resizable=False,
        frameless=True,
        on_top=True,
        background_color="#E8EAF0",
    )
    api.set_window(window)
    window.events.loaded += lambda: api.on_page_loaded()
    window.events.closed += lambda: os._exit(0)
    webview.start(func=api.on_shown, debug=False, http_server=True)


def main():
    # 只用 PySide6 是否可导入来决定路径，不捕获 run_qt() 内部错误
    _qt_ok = False
    try:
        import PySide6
        _qt_ok = True
    except ImportError:
        pass

    if _qt_ok:
        run_qt()   # 任何内部错误都正常抛出，不会默默 fallback
    else:
        print("[FloaTodo] PySide6 未安装，自动降级至 pywebview 模式...")
        run_webview()


if __name__ == "__main__":
    main()
