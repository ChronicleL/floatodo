"""配置读写（JSON 后端）"""
from __future__ import annotations
import json
from pathlib import Path

DEFAULT_SETTINGS = {
    "window_x": -1,        # -1 表示居中/默认
    "window_y": -1,
    "pomodoro_work": 25,
    "pomodoro_short": 5,
    "pomodoro_long": 15,
    "pomodoro_long_every": 4,
    "always_on_top": True,
    "opacity": 1.0,
}

_CONFIG_PATH = Path(__file__).parent.parent / "data" / "settings.json"


def load() -> dict:
    if _CONFIG_PATH.exists():
        try:
            data = json.loads(_CONFIG_PATH.read_text(encoding="utf-8"))
            return {**DEFAULT_SETTINGS, **data}
        except Exception:
            pass
    return dict(DEFAULT_SETTINGS)


def save(settings: dict) -> None:
    _CONFIG_PATH.parent.mkdir(exist_ok=True)
    _CONFIG_PATH.write_text(json.dumps(settings, ensure_ascii=False, indent=2), encoding="utf-8")
