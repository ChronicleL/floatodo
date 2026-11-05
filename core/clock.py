"""实时时钟模块（线程版）：独立后台线程，不依赖 tkinter/GUI。"""
from __future__ import annotations
import threading
import time
from datetime import datetime, date
from typing import Optional
from core.signal import Signal


class ClockCore:
    time_ticked  = None   # Signal(datetime)
    date_changed = None   # Signal(date)

    def __init__(self):
        self.time_ticked  = Signal()
        self.date_changed = Signal()
        self._last_second: int           = -1
        self._last_date:   Optional[date] = None
        self._running = False

    def start(self) -> None:
        if self._running:
            return  # 已在运行，拒绝重复启动（防止 on_shown 多次调用产生多个时钟线程）
        self._running = True
        threading.Thread(target=self._loop, daemon=True, name="clock-core").start()

    def stop(self) -> None:
        self._running = False

    def _loop(self) -> None:
        while self._running:
            now = datetime.now()
            if now.second != self._last_second:
                self._last_second = now.second
                self.time_ticked.emit(now)
                if self._last_date is None or now.date() != self._last_date:
                    self._last_date = now.date()
                    self.date_changed.emit(now.date())
            time.sleep(0.1)
