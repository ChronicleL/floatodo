"""任务秒表计时器：心跳驱动，支持暂停/恢复与累计计时"""
from __future__ import annotations
from datetime import datetime
from typing import Optional
from core.signal import Signal


class TaskTimer:
    def __init__(self):
        self.elapsed_updated = Signal()   # (task_id, elapsed_seconds)
        self._active_task_id: Optional[int] = None
        self._base_elapsed: int = 0
        self._start_time: Optional[datetime] = None

    @property
    def active_task_id(self) -> Optional[int]:
        return self._active_task_id

    def start(self, task_id: int, existing_elapsed: int = 0) -> None:
        self._active_task_id = task_id
        self._base_elapsed = existing_elapsed
        self._start_time = datetime.now()

    def pause(self) -> int:
        total = self._current_elapsed()
        self._base_elapsed = total
        self._start_time = None
        return total

    def stop(self) -> int:
        total = self.pause()
        self._active_task_id = None
        return total

    def on_tick(self) -> None:
        if self._active_task_id is None or self._start_time is None:
            return
        self.elapsed_updated.emit(self._active_task_id, self._current_elapsed())

    def _current_elapsed(self) -> int:
        if self._start_time is None:
            return self._base_elapsed
        delta = (datetime.now() - self._start_time).total_seconds()
        return self._base_elapsed + int(delta)
