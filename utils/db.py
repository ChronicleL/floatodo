"""SQLite 数据库连接管理（单例，WAL 模式）"""
import sys
import sqlite3
import os
from pathlib import Path

_conn: sqlite3.Connection | None = None

if getattr(sys, "frozen", False):
    APP_ROOT = Path(sys.executable).parent
else:
    APP_ROOT = Path(__file__).parent.parent

DB_PATH = APP_ROOT / "data" / "tasks.db"


def get_conn() -> sqlite3.Connection:
    global _conn
    if _conn is None:
        DB_PATH.parent.mkdir(exist_ok=True)
        _conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        _conn.row_factory = sqlite3.Row
        _conn.execute("PRAGMA journal_mode=WAL")
        _conn.execute("PRAGMA synchronous=NORMAL")
        _init_schema(_conn)
    return _conn


def _init_schema(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            title           TEXT    NOT NULL,
            note            TEXT    DEFAULT '',
            priority        INTEGER DEFAULT 0,
            status          TEXT    DEFAULT 'pending',
            elapsed_seconds INTEGER DEFAULT 0,
            created_at      TEXT,
            completed_at    TEXT,
            pomodoro_count  INTEGER DEFAULT 0,
            sort_order      INTEGER DEFAULT 0
        )
    """)
    conn.commit()


def close():
    global _conn
    if _conn:
        _conn.close()
        _conn = None
