"""任务管理模块：CRUD 操作，SQLite 后端，Signal 驱动"""
from __future__ import annotations
from datetime import datetime
from typing import List, Optional

from core.signal import Signal
from core.models import Task, TaskStatus, Priority
from utils.db import get_conn


class TaskManager:
    def __init__(self):
        self.task_added    = Signal()   # Task
        self.task_updated  = Signal()   # Task
        self.task_deleted  = Signal()   # task_id
        self.task_completed = Signal()  # Task

        self._tasks: List[Task] = []
        self._load_all()

    # ── 内部加载 ──────────────────────────────────────────────────────────
    def _load_all(self) -> None:
        conn = get_conn()
        rows = conn.execute(
            "SELECT * FROM tasks WHERE status != 'archived' ORDER BY sort_order, id"
        ).fetchall()
        self._tasks = [self._row_to_task(r) for r in rows]

    @staticmethod
    def _row_to_task(row) -> Task:
        return Task(
            id=row["id"],
            title=row["title"],
            note=row["note"] or "",
            priority=Priority(row["priority"]),
            status=TaskStatus(row["status"]),
            elapsed_seconds=row["elapsed_seconds"],
            created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else datetime.now(),
            completed_at=datetime.fromisoformat(row["completed_at"]) if row["completed_at"] else None,
            pomodoro_count=row["pomodoro_count"],
        )

    # ── 公开 API ──────────────────────────────────────────────────────────
    @property
    def tasks(self) -> List[Task]:
        return list(self._tasks)

    def add_task(self, title: str, note: str = "", priority: Priority = Priority.NORMAL) -> Task:
        conn = get_conn()
        now = datetime.now().isoformat()
        cur = conn.execute(
            "INSERT INTO tasks (title, note, priority, status, created_at, sort_order) VALUES (?,?,?,?,?,?)",
            (title, note, int(priority), TaskStatus.PENDING.value, now, len(self._tasks))
        )
        conn.commit()
        task = Task(
            id=cur.lastrowid,
            title=title,
            note=note,
            priority=priority,
            status=TaskStatus.PENDING,
            created_at=datetime.now(),
        )
        self._tasks.append(task)
        self.task_added.emit(task)
        return task

    def complete_task(self, task_id: int) -> Optional[Task]:
        task = self._find(task_id)
        if task is None or task.is_completed:
            return None
        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.now()
        conn = get_conn()
        conn.execute(
            "UPDATE tasks SET status=?, completed_at=? WHERE id=?",
            (TaskStatus.COMPLETED.value, task.completed_at.isoformat(), task_id)
        )
        conn.commit()
        self.task_completed.emit(task)
        self.task_updated.emit(task)
        return task

    def uncomplete_task(self, task_id: int) -> Optional[Task]:
        task = self._find(task_id)
        if task is None:
            return None
        task.status = TaskStatus.PENDING
        task.completed_at = None
        conn = get_conn()
        conn.execute(
            "UPDATE tasks SET status=?, completed_at=NULL WHERE id=?",
            (TaskStatus.PENDING.value, task_id)
        )
        conn.commit()
        self.task_updated.emit(task)
        return task

    def delete_task(self, task_id: int) -> bool:
        task = self._find(task_id)
        if task is None:
            return False
        self._tasks.remove(task)
        conn = get_conn()
        conn.execute("DELETE FROM tasks WHERE id=?", (task_id,))
        conn.commit()
        self.task_deleted.emit(task_id)
        return True

    def update_elapsed(self, task_id: int, elapsed_seconds: int) -> None:
        task = self._find(task_id)
        if task is None:
            return
        task.elapsed_seconds = elapsed_seconds
        conn = get_conn()
        conn.execute("UPDATE tasks SET elapsed_seconds=? WHERE id=?", (elapsed_seconds, task_id))
        conn.commit()

    def increment_pomodoro(self, task_id: int) -> None:
        task = self._find(task_id)
        if task is None:
            return
        task.pomodoro_count += 1
        conn = get_conn()
        conn.execute("UPDATE tasks SET pomodoro_count=? WHERE id=?", (task.pomodoro_count, task_id))
        conn.commit()

    def _find(self, task_id: int) -> Optional[Task]:
        for t in self._tasks:
            if t.id == task_id:
                return t
        return None
