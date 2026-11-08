"""配置读写（JSON 后端）"""
from __future__ import annotations
import sys
import json
from pathlib import Path

DEFAULT_SETTINGS = {
    "window_x": -1,        # -1 表示居中/默认
    "window_y": -1,
    "pomodoro_work": 25,   # 专注时长（分钟）
    "pomodoro_short": 5,   # 短休时长（分钟）
    "pomodoro_long": 15,   # 长休时长（分钟）
    "pomodoro_long_every": 4, # 完整轮数（每 N 轮后长休并奖励番茄）
    "sound_enabled": True, # 是否启用声音提示
    "sound_max_duration": 3, # 自定义音效播放时间上限（秒，超时自动卡断）
    "sound_custom_next": "", # 自定义下一阶段提示音路径（为空则使用默认）
    "sound_custom_done": "", # 自定义大满贯完成提示音路径（为空则使用默认）
    "always_on_top": True,
    "opacity": 1.0,
    "total_tomatoes": 0,   # 累计收获的番茄总数
}

if getattr(sys, "frozen", False):
    APP_ROOT = Path(sys.executable).parent
else:
    APP_ROOT = Path(__file__).parent.parent

_CONFIG_PATH = APP_ROOT / "data" / "settings.json"


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
