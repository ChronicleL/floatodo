"""
FloaTodo — 融合 Windows 专注风格与新拟态的专注表盘组件
纯净专注视觉：去除具体时钟，统一居中显示 MM:SS（如 25:00），支持完成光环波纹动效
"""
import math
from PySide6.QtCore import Qt, QRectF, QPointF, Signal, QTimer
from PySide6.QtWidgets import QWidget
from PySide6.QtGui import (
    QPainter, QColor, QPen, QBrush, QFont, QLinearGradient
)

from ui_qt.styles import (
    COLOR_SD, COLOR_SL, COLOR_TEXT_PRI, COLOR_TEXT_SEC, COLOR_TEXT_MUTED,
    ACCENT_WORK, ACCENT_SHORT, ACCENT_LONG, ACCENT_IDLE
)


class FocusDial(QWidget):
    clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(180, 180)
        self.setMaximumSize(320, 320)

        # 状态数据
        self._phase = "idle"              # 'work', 'short', 'long', 'idle'
        self._total_seconds = 25 * 60     # 当前阶段总秒数
        self._remaining_seconds = 25 * 60 # 剩余秒数
        self._is_running = False

        # 完成波纹动效状态
        self._ripple_radius = 0.0
        self._ripple_opacity = 0.0
        self._ripple_timer = QTimer(self)
        self._ripple_timer.setInterval(25)
        self._ripple_timer.timeout.connect(self._step_ripple)

        self._tick_count = 30             # 30 个刻度，通透简洁
        self.setCursor(Qt.PointingHandCursor)

    def set_phase(self, phase: str, total_seconds: int):
        self._phase = phase
        self._total_seconds = max(1, total_seconds)
        self._remaining_seconds = total_seconds
        self.update()

    def set_tick(self, remaining_seconds: int, total_seconds: int):
        self._remaining_seconds = remaining_seconds
        self._total_seconds = max(1, total_seconds)
        self.update()

    def set_running(self, running: bool):
        self._is_running = running
        self.update()

    def trigger_completion_ripple(self):
        """阶段完成时触发向外扩散的发光水波纹动效"""
        self._ripple_radius = 0.1
        self._ripple_opacity = 0.85
        self._ripple_timer.start()

    def _step_ripple(self):
        self._ripple_radius += 0.04
        self._ripple_opacity -= 0.035
        if self._ripple_opacity <= 0.0 or self._ripple_radius >= 1.4:
            self._ripple_timer.stop()
            self._ripple_opacity = 0.0
            self._ripple_radius = 0.0
        self.update()

    def get_phase_color(self) -> QColor:
        if self._phase == "work":
            return QColor(ACCENT_WORK)
        elif self._phase == "short":
            return QColor(ACCENT_SHORT)
        elif self._phase == "long":
            return QColor(ACCENT_LONG)
        return QColor(ACCENT_IDLE)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)

        w = self.width()
        h = self.height()
        center_x = w / 2.0
        center_y = h / 2.0
        radius = min(w, h) / 2.0 - 10.0
        if radius < 30:
            return

        accent_color = self.get_phase_color()

        # 0. 绘制阶段完成向外扩散的光环波纹（Ripple）
        if self._ripple_opacity > 0.0:
            ripple_r = radius * (0.8 + self._ripple_radius * 0.4)
            ripple_color = QColor(accent_color)
            ripple_color.setAlphaF(max(0.0, min(1.0, self._ripple_opacity)))
            ripple_pen = QPen(ripple_color, 4.0 * self._ripple_opacity)
            painter.setPen(ripple_pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(QPointF(center_x, center_y), ripple_r, ripple_r)

        # 1. 绘制新拟态外凸/微内凹圆形底盘
        painter.setPen(Qt.NoPen)
        painter.setBrush(COLOR_SL)
        painter.drawEllipse(QPointF(center_x - 3, center_y - 3), radius + 1, radius + 1)

        painter.setBrush(COLOR_SD)
        painter.drawEllipse(QPointF(center_x + 3, center_y + 3), radius + 1, radius + 1)

        base_grad = QLinearGradient(center_x - radius, center_y - radius, center_x + radius, center_y + radius)
        base_grad.setColorAt(0.0, QColor("#EFF1F6"))
        base_grad.setColorAt(1.0, QColor("#E1E4EC"))
        painter.setBrush(base_grad)
        painter.drawEllipse(QPointF(center_x, center_y), radius, radius)

        # 2. 计算当前进度
        if self._phase == "idle" or self._total_seconds <= 0:
            progress = 0.0
        else:
            progress = max(0.0, min(1.0, 1.0 - (self._remaining_seconds / self._total_seconds)))

        # 3. 绘制刻度环 (Radial Ticks)
        tick_inner = radius * 0.72
        tick_outer = radius * 0.88
        tick_pen_inactive = QPen(QColor(174, 174, 192, 115), 3.0, Qt.SolidLine, Qt.RoundCap)
        tick_pen_active = QPen(accent_color, 3.5, Qt.SolidLine, Qt.RoundCap)

        for i in range(self._tick_count):
            fraction = i / float(self._tick_count)
            angle_rad = math.radians(-90.0 + fraction * 360.0)
            cos_a = math.cos(angle_rad)
            sin_a = math.sin(angle_rad)

            p1 = QPointF(center_x + tick_inner * cos_a, center_y + tick_inner * sin_a)
            p2 = QPointF(center_x + tick_outer * cos_a, center_y + tick_outer * sin_a)

            if self._is_running and fraction <= progress and self._phase != "idle":
                painter.setPen(tick_pen_active)
            else:
                painter.setPen(tick_pen_inactive)

            painter.drawLine(p1, p2)

        # 4. 绘制当前进度指示胶囊（Windows 专注表盘标志性横向进度条）
        if self._phase != "idle" and self._total_seconds > 0:
            indicator_angle_deg = -90.0 + progress * 360.0
            ind_rad = math.radians(indicator_angle_deg)
            ind_dist = (tick_inner + tick_outer) / 2.0
            ind_cx = center_x + ind_dist * math.cos(ind_rad)
            ind_cy = center_y + ind_dist * math.sin(ind_rad)

            painter.save()
            painter.translate(ind_cx, ind_cy)
            painter.rotate(indicator_angle_deg + 90.0)

            pill_w = radius * 0.18
            pill_h = radius * 0.08

            glow = QColor(accent_color)
            glow.setAlpha(80)
            painter.setPen(Qt.NoPen)
            painter.setBrush(glow)
            painter.drawRoundedRect(QRectF(-pill_w / 2 - 2, -pill_h / 2 - 2, pill_w + 4, pill_h + 4), pill_h / 2, pill_h / 2)

            painter.setBrush(accent_color)
            painter.drawRoundedRect(QRectF(-pill_w / 2, -pill_h / 2, pill_w, pill_h), pill_h / 2, pill_h / 2)
            painter.restore()

        # 5. 中心倒计时显示（MM:SS）
        painter.setPen(COLOR_TEXT_PRI)
        m = self._remaining_seconds // 60
        s = self._remaining_seconds % 60
        main_text = f"{m:02d}:{s:02d}"

        # 自适应字体大小，确保不会超出中心圈
        font_size = max(13, int(radius * 0.30))
        font_main = QFont("Segoe UI Variable Display", font_size, QFont.Bold)
        painter.setFont(font_main)

        # 完美垂直+水平居中于表盘圆心
        inner_box = QRectF(center_x - radius * 0.65, center_y - radius * 0.65, radius * 1.3, radius * 1.3)
        painter.drawText(inner_box, Qt.AlignCenter, main_text)
