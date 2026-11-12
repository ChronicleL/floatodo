"""
FloaTodo — Win32 DWM 毛玻璃特效
通过 SetWindowCompositionAttribute 启用/关闭 DWM BlurBehind。
不调用 SetLayeredWindowAttributes(LWA_ALPHA)，避免与 Qt
WA_TranslucentBackground 内部的 UpdateLayeredWindowIndirect 冲突。
"""
from __future__ import annotations
import ctypes
import ctypes.wintypes as wt


# ── DWM 亚克力/毛玻璃 ────────────────────────────────────────────────

class _ACCENTPOLICY(ctypes.Structure):
    _fields_ = [
        ("AccentState",   ctypes.c_uint),
        ("AccentFlags",   ctypes.c_uint),
        ("GradientColor", ctypes.c_uint),
        ("AnimationId",   ctypes.c_uint),
    ]

class _WINDOWCOMPOSITIONATTRIBDATA(ctypes.Structure):
    _fields_ = [
        ("Attribute",  ctypes.c_int),
        ("Data",       ctypes.c_void_p),
        ("SizeOfData", ctypes.c_size_t),
    ]

_WCA_ACCENT               = 19
_ACCENT_DISABLED          = 0
_ACCENT_ENABLE_BLURBEHIND = 3


def _set_accent(hwnd: int, state: int, color: int) -> None:
    """SetWindowCompositionAttribute（ACCENT）."""
    try:
        accent = _ACCENTPOLICY()
        accent.AccentState   = state
        accent.AccentFlags   = 0
        accent.GradientColor = color
        accent.AnimationId   = 0

        data = _WINDOWCOMPOSITIONATTRIBDATA()
        data.Attribute  = _WCA_ACCENT
        data.Data       = ctypes.addressof(accent)
        data.SizeOfData = ctypes.sizeof(accent)

        fn = ctypes.windll.user32.SetWindowCompositionAttribute
        fn.argtypes = [wt.HWND, ctypes.POINTER(_WINDOWCOMPOSITIONATTRIBDATA)]
        fn.restype  = ctypes.c_bool
        fn(hwnd, ctypes.byref(data))
    except Exception as e:
        print(f"[Effects] accent error: {e}")


def enable_glass(hwnd: int) -> None:
    """启用毛玻璃 DWM 模糊帧。
    Qt 窗口已设 WA_TranslucentBackground，内部用 UpdateLayeredWindowIndirect 管理。
    SetLayeredWindowAttributes(LWA_ALPHA) 与 UpdateLayeredWindowIndirect 互斥，
    绝不能调用，否则每帧都会报 UpdateLayeredWindowIndirect failed。
    此处只调用 SetWindowCompositionAttribute 添加 DWM BlurBehind 效果。
    实际透明度由 CSS 卡片背景的 rgba() 控制。"""
    _set_accent(hwnd, _ACCENT_ENABLE_BLURBEHIND, 0x01000000)


def disable_glass(hwnd: int) -> None:
    """关闭 DWM 模糊帧。"""
    _set_accent(hwnd, _ACCENT_DISABLED, 0)
