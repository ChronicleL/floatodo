"""轻量级信号/回调系统（替代 Qt Signal，零依赖）"""
from __future__ import annotations
from typing import Callable, List, Any


class Signal:
    """简单的观察者模式 Signal，兼容 Qt Signal 的 connect/emit API"""

    def __init__(self):
        self._callbacks: List[Callable] = []

    def connect(self, callback: Callable) -> None:
        if callback not in self._callbacks:
            self._callbacks.append(callback)

    def disconnect(self, callback: Callable) -> None:
        try:
            self._callbacks.remove(callback)
        except ValueError:
            pass

    def emit(self, *args: Any) -> None:
        for cb in list(self._callbacks):
            try:
                cb(*args)
            except Exception as e:
                print(f"[Signal] callback error: {e}")
