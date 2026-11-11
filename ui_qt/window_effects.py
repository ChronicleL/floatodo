"""
FloaTodo — Win32 窗口特效
提供毛玻璃（DWM 亚克力 + LWA_ALPHA）和边缘拖拽缩放辅助
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

_GWL_EXSTYLE    = -20
_WS_EX_LAYERED  = 0x00080000
_LWA_ALPHA      = 0x02
_WCA_ACCENT     = 19
_ACCENT_DISABLED            = 0
_ACCENT_ENABLE_BLURBEHIND   = 3
_ACCENT_ENABLE_ACRYLIC      = 4


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


def enable_glass(hwnd: int, alpha: int = 215) -> None:
    """启用毛玻璃：LWA_ALPHA 实现真实透明（桌面穿透）+ DWM 模糊帧。
    alpha=215 → 窗口 84% 不透明，桌面可见 16%。"""
    try:
        ex = ctypes.windll.user32.GetWindowLongW(hwnd, _GWL_EXSTYLE)
        ctypes.windll.user32.SetWindowLongW(hwnd, _GWL_EXSTYLE, ex | _WS_EX_LAYERED)
        ctypes.windll.user32.SetLayeredWindowAttributes(hwnd, 0, int(alpha), _LWA_ALPHA)
    except Exception as e:
        print(f"[Effects] LWA_ALPHA error: {e}")
    _set_accent(hwnd, _ACCENT_ENABLE_BLURBEHIND, 0x01000000)


def disable_glass(hwnd: int) -> None:
    """关闭毛玻璃，恢复完全不透明。"""
    try:
        ex = ctypes.windll.user32.GetWindowLongW(hwnd, _GWL_EXSTYLE)
        if ex & _WS_EX_LAYERED:
            ctypes.windll.user32.SetLayeredWindowAttributes(hwnd, 0, 255, _LWA_ALPHA)
    except Exception as e:
        print(f"[Effects] restore error: {e}")
    _set_accent(hwnd, _ACCENT_DISABLED, 0)


# ── WM_NCHITTEST 返回值 ──────────────────────────────────────────────
HTLEFT        = 10
HTRIGHT       = 11
HTTOP         = 12
HTTOPLEFT     = 13
HTTOPRIGHT    = 14
HTBOTTOM      = 15
HTBOTTOMLEFT  = 16
HTBOTTOMRIGHT = 17


def hit_test_edges(x: int, y: int, w: int, h: int, border: int = 7) -> int | None:
    """给定鼠标相对窗口坐标，返回 HTXXX 常量或 None（非边缘区域）。"""
    on_left   = x < border
    on_right  = x > w - border
    on_top    = y < border
    on_bottom = y > h - border

    if on_top    and on_left:  return HTTOPLEFT
    if on_top    and on_right: return HTTOPRIGHT
    if on_bottom and on_left:  return HTBOTTOMLEFT
    if on_bottom and on_right: return HTBOTTOMRIGHT
    if on_left:                return HTLEFT
    if on_right:               return HTRIGHT
    if on_top:                 return HTTOP
    if on_bottom:              return HTBOTTOM
    return None


# ── WM_SIZING 维持长宽比 ─────────────────────────────────────────────
# wParam 值
WMSZ_LEFT        = 1
WMSZ_RIGHT       = 2
WMSZ_TOP         = 3
WMSZ_TOPLEFT     = 4
WMSZ_TOPRIGHT    = 5
WMSZ_BOTTOM      = 6
WMSZ_BOTTOMLEFT  = 7
WMSZ_BOTTOMRIGHT = 8


def constrain_sizing_rect(
    side: int,
    rect_ptr,           # ctypes POINTER(RECT)
    aspect: float,      # height / width
    min_w: int,
    max_w: int,
    dpr: float = 1.0,
) -> None:
    """在 WM_SIZING 处理中原地修改 RECT，强制维持 aspect = H/W 比例并约束范围。
    rect_ptr 是 ctypes POINTER(RECT)，单位为物理像素。"""
    r = rect_ptr.contents
    min_w_p = int(min_w * dpr)
    max_w_p = int(max_w * dpr)
    min_h_p = int(min_w_p * aspect)
    max_h_p = int(max_w_p * aspect)

    new_w = r.right - r.left
    new_h = r.bottom - r.top

    # 确定 target 尺寸（宽优先）
    if side in (WMSZ_TOP, WMSZ_BOTTOM):
        # 高度拖拽：先 clamp 高，再推导宽
        target_h = max(min_h_p, min(max_h_p, new_h))
        target_w = int(target_h / aspect)
    else:
        # 宽度拖拽（边或角）：先 clamp 宽，再推导高
        target_w = max(min_w_p, min(max_w_p, new_w))
        target_h = int(target_w * aspect)

    # 根据拖拽方向更新 RECT
    if side in (WMSZ_LEFT, WMSZ_TOPLEFT, WMSZ_BOTTOMLEFT):
        r.left = r.right - target_w
    else:
        r.right = r.left + target_w

    if side in (WMSZ_TOP, WMSZ_TOPLEFT, WMSZ_TOPRIGHT):
        r.top = r.bottom - target_h
    else:
        r.bottom = r.top + target_h
