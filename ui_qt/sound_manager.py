"""
FloaTodo — 音效管理系统
支持 Windows 系统内置悦耳音效与自主导入本地音频（.wav/.mp3/.m4a/.flac 等），
并具备超时自动卡断机制，防止导入的长音频持续播放打扰工作。
"""
import os
import winsound
from pathlib import Path
from PySide6.QtCore import QObject, QUrl, QTimer

# QtMultimedia 是可选依赖（pyside6-addons 提供），不可用时降级为系统音
try:
    from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
    _HAS_MULTIMEDIA = True
except ImportError:
    _HAS_MULTIMEDIA = False


class SoundManager(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._player = None
        self._audio_output = None
        self._cutoff_timer = QTimer(self)
        self._cutoff_timer.setSingleShot(True)
        self._cutoff_timer.timeout.connect(self.stop)

        if _HAS_MULTIMEDIA:
            self._player = QMediaPlayer(self)
            self._audio_output = QAudioOutput(self)
            self._player.setAudioOutput(self._audio_output)

    def play(self, sound_type: str, cfg: dict):
        """
        播放指定类型的音效：
        sound_type: 'next' (阶段流转) 或 'done' (大满贯完成)
        """
        if not cfg.get("sound_enabled", True):
            return

        custom_path = cfg.get("sound_custom_done" if sound_type == "done" else "sound_custom_next", "").strip()
        max_duration = max(1, int(cfg.get("sound_max_duration", 3)))

        if custom_path and os.path.exists(custom_path) and _HAS_MULTIMEDIA:
            self.play_file(custom_path, max_duration)
        else:
            # 使用 Windows 系统内置默认通知音（无需 QtMultimedia）
            try:
                alias = "SystemAsterisk" if sound_type == "next" else "SystemExclamation"
                winsound.PlaySound(alias, winsound.SND_ALIAS | winsound.SND_ASYNC)
            except Exception:
                pass

    def play_file(self, file_path: str, max_duration_sec: int = 3):
        """播放本地自定义音频（需要 QtMultimedia），超时自动卡断"""
        if not _HAS_MULTIMEDIA or self._player is None:
            return
        self.stop()
        if not file_path or not os.path.exists(file_path):
            return

        url = QUrl.fromLocalFile(file_path)
        self._player.setSource(url)
        self._audio_output.setVolume(0.85)
        self._player.play()
        self._cutoff_timer.start(int(max_duration_sec * 1000))

    def stop(self):
        """立即停止播放与卡断计时"""
        self._cutoff_timer.stop()
        if _HAS_MULTIMEDIA and self._player is not None:
            if self._player.playbackState() == QMediaPlayer.PlayingState:
                self._player.stop()


# 单例实例
_sound_mgr = None

def get_sound_manager() -> SoundManager:
    global _sound_mgr
    if _sound_mgr is None:
        _sound_mgr = SoundManager()
    return _sound_mgr
