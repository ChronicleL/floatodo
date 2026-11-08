"""数据模型定义"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from enum import Enum


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class Priority(int, Enum):
    NORMAL = 0
    IMPORTANT = 1
    URGENT = 2


class PomodoroPhase(str, Enum):
    IDLE = "idle"
    WORK = "work"
    SHORT_BREAK = "short"
    LONG_BREAK = "long"


@dataclass
class Task:
    id: int = 0
    title: str = ""
    note: str = ""
    priority: Priority = Priority.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    elapsed_seconds: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    pomodoro_count: int = 0

    @property
    def is_completed(self) -> bool:
        return self.status == TaskStatus.COMPLETED

    def elapsed_str(self) -> str:
        """格式化累计计时"""
        h = self.elapsed_seconds // 3600
        m = (self.elapsed_seconds % 3600) // 60
        s = self.elapsed_seconds % 60
        if h > 0:
            return f"{h}:{m:02d}:{s:02d}"
        return f"{m}:{s:02d}"


@dataclass
class PomodoroSession:
    phase: PomodoroPhase = PomodoroPhase.IDLE
    work_duration: int = 25 * 60    # 秒
    short_duration: int = 5 * 60
    long_duration: int = 15 * 60
    completed_rounds: int = 0        # 已完成的 work 轮次
    long_break_every: int = 4        # 每 N 个 work 后长休

    @property
    def current_duration(self) -> int:
        return {
            PomodoroPhase.WORK: self.work_duration,
            PomodoroPhase.SHORT_BREAK: self.short_duration,
            PomodoroPhase.LONG_BREAK: self.long_duration,
            PomodoroPhase.IDLE: self.work_duration,  # 就绪状态下默认显示单次专注时长
        }[self.phase]
