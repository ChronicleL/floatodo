"""FloaTodo — 应用主入口（PySide6 原生 UI）"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ── conda 环境 DLL 路径修复 ──────────────────────────────────────────
# conda 编译的 PySide6 依赖 <conda_root>/Library/bin 里的 Qt DLL。
# IDE / 双击启动时 conda activate 未运行，需手动加入搜索路径。
def _ensure_conda_dll_path() -> None:
    # 仅在 conda 直接环境（非 venv）下注入 Library/bin
    in_venv = sys.prefix != sys.base_prefix
    if in_venv:
        return
    lib_bin = os.path.join(sys.base_prefix, "Library", "bin")
    if os.path.isdir(lib_bin):
        try:
            os.add_dll_directory(lib_bin)
        except Exception:
            pass
        current = os.environ.get("PATH", "")
        if lib_bin.lower() not in current.lower():
            os.environ["PATH"] = lib_bin + os.pathsep + current

_ensure_conda_dll_path()


def main():
    from main_qt import main as qt_main
    qt_main()


if __name__ == "__main__":
    main()
