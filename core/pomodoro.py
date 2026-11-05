"""番茄钟状态机（tkinter 版）：IDLE→WORK→SHORT_BREAK→LONG_BREAK"""
from __future__ import annotations
from core.models import PomodoroPhase, PomodoroSession
from core.signal import Signal


class PomodoroCore:
    def __init__(self):
        self.tick = Signal()              # (remaining, total)
        self.phase_changed = Signal()     # (phase_value, duration)
        self.session_completed = Signal() # (rounds)
        self.pomodoro_finished = Signal() # ()

        self._session = PomodoroSession()
        self._remaining: int = 0
        self._running: bool = False

    @property
    def phase(self) -> PomodoroPhase:
        return self._session.phase

    @property
    def remaining(self) -> int:
        return self._remaining

    @property
    def total(self) -> int:
        return self._session.current_duration

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def completed_rounds(self) -> int:
        return self._session.completed_rounds

    def start(self) -> None:
        if self._session.phase == PomodoroPhase.IDLE:
            self._enter_phase(PomodoroPhase.WORK)
        self._running = True

    def pause(self) -> None:
        self._running = False

    def skip(self) -> None:
        self._advance_phase()

    def reset(self) -> None:
        self._running = False
        self._session.completed_rounds = 0
        self._enter_phase(PomodoroPhase.IDLE)

    def configure(self, work: int = 25, short: int = 5, long: int = 15, long_every: int = 4) -> None:
        self._session.work_duration = work * 60
        self._session.short_duration = short * 60
        self._session.long_duration = long * 60
        self._session.long_break_every = long_every

    def on_tick(self) -> None:
        """每秒由 ClockCore.time_ticked 驱动"""
        if not self._running or self._session.phase == PomodoroPhase.IDLE:
            return
        self._remaining -= 1
        self.tick.emit(self._remaining, self._session.current_duration)
        if self._remaining <= 0:
            self._on_phase_end()

    def _on_phase_end(self) -> None:
        if self._session.phase == PomodoroPhase.WORK:
            self._session.completed_rounds += 1
            self.pomodoro_finished.emit()
            self.session_completed.emit(self._session.completed_rounds)
        self._advance_phase()

    def _advance_phase(self) -> None:
        current = self._session.phase
        if current == PomodoroPhase.IDLE:
            self._enter_phase(PomodoroPhase.WORK)
        elif current == PomodoroPhase.WORK:
            rounds = self._session.completed_rounds
            if rounds > 0 and rounds % self._session.long_break_every == 0:
                self._enter_phase(PomodoroPhase.LONG_BREAK)
            else:
                self._enter_phase(PomodoroPhase.SHORT_BREAK)
        else:
            self._enter_phase(PomodoroPhase.WORK)

    def _enter_phase(self, phase: PomodoroPhase) -> None:
        self._session.phase = phase
        self._remaining = self._session.current_duration
        self.phase_changed.emit(phase.value, self._remaining)
        if phase == PomodoroPhase.IDLE:
            self._running = False
