"""
FloaTodo — 纯矢量新拟态控制按钮与动态图钉组件
彻底替代文字 Emoji，保证 Windows 任何缩放与主题下色彩统一、清晰抗锯齿
"""
from enum import Enum
from PySide6.QtCore import Qt, QRectF, QPointF, Property, QPropertyAnimation, QEasingCurve
from PySide6.QtWidgets import QPushButton
from PySide6.QtGui import (
    QPainter, QColor, QPen, QBrush, QPolygonF
)

from ui_qt.styles import (
    COLOR_SD, COLOR_SL, COLOR_TEXT_PRI, COLOR_TEXT_SEC, COLOR_TEXT_MUTED,
    ACCENT_WORK, BG_HEX, BG_PRESSED_HEX
)


class IconType(Enum):
    PLAY = "play"
    PAUSE = "pause"
    SKIP = "skip"
    MORE = "more"


class RoundIconButton(QPushButton):
    """
    纯矢量绘制的圆形新拟态按钮，支持开始/暂停、跳过(>>)、更多(...)
    """
    def __init__(self, icon_type: IconType = IconType.PLAY, size: int = 40, is_accent: bool = False, parent=None):
        super().__init__(parent)
        self._icon_type = icon_type
        self._size = size
        self._is_accent = is_accent  # 是否为主强调色背景
        self._is_hover = False
        self._is_pressed = False

        self.setFixedSize(size, size)
        self.setCursor(Qt.PointingHandCursor)

    def set_icon_type(self, icon_type: IconType, is_accent: bool = False):
        self._icon_type = icon_type
        self._is_accent = is_accent
        self.update()

    def enterEvent(self, event):
        self._is_hover = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._is_hover = False
        self._is_pressed = False
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._is_pressed = True
            self.update()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._is_pressed = False
            self.update()
        super().mouseReleaseEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()
        cx = w / 2.0
        cy = h / 2.0
        r = min(w, h) / 2.0 - 2.0

        # 1. 绘制拟态底盘
        if self._is_accent:
            base_color = QColor("#6C5EAF") if self._is_pressed else (QColor("#897AC8") if self._is_hover else QColor(ACCENT_WORK))
            painter.setPen(Qt.NoPen)
            painter.setBrush(base_color)
            painter.drawEllipse(QPointF(cx, cy), r, r)
            icon_color = QColor("#FFFFFF")
        else:
            if not self._is_pressed:
                painter.setPen(Qt.NoPen)
                painter.setBrush(COLOR_SL)
                painter.drawEllipse(QPointF(cx - 1.5, cy - 1.5), r, r)
                painter.setBrush(COLOR_SD)
                painter.drawEllipse(QPointF(cx + 1.5, cy + 1.5), r, r)

            bg_c = QColor("#D8DAE2") if self._is_pressed else (QColor("#F0F2F7") if self._is_hover else QColor("#E2E5EC"))
            painter.setPen(QPen(QColor(174, 174, 192, 90), 1))
            painter.setBrush(bg_c)
            painter.drawEllipse(QPointF(cx, cy), r - 1.0, r - 1.0)
            icon_color = QColor(ACCENT_WORK) if self._is_hover else QColor(COLOR_TEXT_PRI)

        # 2. 纯矢量绘制图标
        painter.setPen(Qt.NoPen)
        painter.setBrush(icon_color)

        if self._icon_type == IconType.PLAY:
            # 居中三角形 ▶
            s = r * 0.52
            p1 = QPointF(cx - s * 0.45 + 1.5, cy - s * 0.6)
            p2 = QPointF(cx + s * 0.65 + 1.5, cy)
            p3 = QPointF(cx - s * 0.45 + 1.5, cy + s * 0.6)
            poly = QPolygonF([p1, p2, p3])
            painter.drawPolygon(poly)

        elif self._icon_type == IconType.PAUSE:
            # 两个圆角竖条 ❚❚
            bar_w = r * 0.22
            bar_h = r * 0.72
            gap = r * 0.20
            painter.drawRoundedRect(QRectF(cx - gap / 2 - bar_w, cy - bar_h / 2, bar_w, bar_h), bar_w / 2, bar_w / 2)
            painter.drawRoundedRect(QRectF(cx + gap / 2, cy - bar_h / 2, bar_w, bar_h), bar_w / 2, bar_w / 2)

        elif self._icon_type == IconType.SKIP:
            # 纯色矢量双右箭头 »
            tri_w = r * 0.32
            tri_h = r * 0.48
            gap = r * 0.08
            p1 = QPointF(cx - tri_w - gap / 2, cy - tri_h / 2)
            p2 = QPointF(cx - gap / 2, cy)
            p3 = QPointF(cx - tri_w - gap / 2, cy + tri_h / 2)
            painter.drawPolygon(QPolygonF([p1, p2, p3]))

            p4 = QPointF(cx + gap / 2, cy - tri_h / 2)
            p5 = QPointF(cx + tri_w + gap / 2, cy)
            p6 = QPointF(cx + gap / 2, cy + tri_h / 2)
            painter.drawPolygon(QPolygonF([p4, p5, p6]))

        elif self._icon_type == IconType.MORE:
            # 三个纯色圆点 ···
            dot_r = r * 0.12
            spacing = r * 0.34
            painter.drawEllipse(QPointF(cx - spacing, cy), dot_r, dot_r)
            painter.drawEllipse(QPointF(cx, cy), dot_r, dot_r)
            painter.drawEllipse(QPointF(cx + spacing, cy), dot_r, dot_r)


class PinButton(QPushButton):
    """
    精致微型图钉按钮：尺寸与标题栏其他系统按键 100% 对齐（26×26）
    支持平滑缓动旋转动画：
    - 置顶状态：垂直下钉（0°），高亮醒目紫色
    - 取消置顶：拔起倾斜（45°），柔和灰色
    """
    def __init__(self, is_pinned: bool = True, parent=None):
        super().__init__(parent)
        self.setFixedSize(26, 26)
        self.setCursor(Qt.PointingHandCursor)
        self._is_pinned = is_pinned
        self._angle = 0.0 if is_pinned else 45.0
        self._is_hover = False

        self._anim = QPropertyAnimation(self, b"angle")
        self._anim.setDuration(220)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)

        self._update_tooltip()

    def get_angle(self) -> float:
        return self._angle

    def set_angle(self, a: float):
        self._angle = a
        self.update()

    angle = Property(float, get_angle, set_angle)

    def set_pinned(self, pinned: bool):
        if self._is_pinned != pinned:
            self._is_pinned = pinned
            self._update_tooltip()
            self._anim.stop()
            self._anim.setStartValue(self._angle)
            self._anim.setEndValue(0.0 if pinned else 45.0)
            self._anim.start()

    def _update_tooltip(self):
        self.setToolTip("保持置顶（点击取消）" if self._is_pinned else "点击保持置顶")

    def enterEvent(self, event):
        self._is_hover = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._is_hover = False
        self.update()
        super().leaveEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()
        cx = w / 2.0
        cy = h / 2.0

        # 悬停轻微背景反馈
        if self._is_hover:
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(BG_PRESSED_HEX))
            painter.drawRoundedRect(QRectF(1, 1, w - 2, h - 2), 6, 6)

        painter.save()
        painter.translate(cx, cy)
        painter.rotate(self._angle)

        # 颜色计算：平滑过渡
        t = (45.0 - self._angle) / 45.0
        t = max(0.0, min(1.0, t))
        pin_color = QColor(
            int(160 + (124 - 160) * t),
            int(174 + (110 - 174) * t),
            int(192 + (190 - 192) * t)
        )

        # 缩放至与 12px 字体完美协调的图钉矢量尺寸（高度 ~12.5px，宽度 ~7px）
        # 1. 针尖（下方细线）
        pen_needle = QPen(pin_color, 1.4, Qt.SolidLine, Qt.RoundCap)
        painter.setPen(pen_needle)
        painter.drawLine(QPointF(0, 0), QPointF(0, 5.5))

        # 2. 针托底部横条
        painter.setPen(Qt.NoPen)
        painter.setBrush(pin_color)
        painter.drawRoundedRect(QRectF(-3.5, -1.5, 7, 1.8), 0.8, 0.8)

        # 3. 钉身锥体/圆柱
        painter.drawRoundedRect(QRectF(-1.8, -5.5, 3.6, 4), 0.8, 0.8)

        # 4. 钉帽大圆顶
        painter.drawRoundedRect(QRectF(-3.2, -7.5, 6.4, 2), 1, 1)

        painter.restore()
