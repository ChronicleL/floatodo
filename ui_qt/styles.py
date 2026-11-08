"""
FloaTodo — 原生 Neumorphic 新拟态样式与视觉规范
"""
from PySide6.QtGui import QColor, QFont

# 基础调色板
BG_HEX = "#E8EAF0"
BG_HOVER_HEX = "#ECEEF5"
BG_PRESSED_HEX = "#D8DAE2"

TEXT_PRI_HEX = "#2D3748"
TEXT_SEC_HEX = "#718096"
TEXT_MUTED_HEX = "#A0AEC0"

ACCENT_WORK = "#7C6EBE"    # 专注紫
ACCENT_SHORT = "#56AB91"   # 短休绿
ACCENT_LONG = "#5E9FF2"    # 长休蓝
ACCENT_IDLE = "#A0AEC0"    # 空闲灰
COLOR_RED = "#E07070"
COLOR_AMBER = "#E6A817"

# QColor 对象
COLOR_BG = QColor(BG_HEX)
COLOR_BG_HOVER = QColor(BG_HOVER_HEX)
COLOR_BG_PRESSED = QColor(BG_PRESSED_HEX)
COLOR_TEXT_PRI = QColor(TEXT_PRI_HEX)
COLOR_TEXT_SEC = QColor(TEXT_SEC_HEX)
COLOR_TEXT_MUTED = QColor(TEXT_MUTED_HEX)

# 阴影与高光
COLOR_SD = QColor(174, 174, 192, 105)   # 暗部阴影
COLOR_SL = QColor(255, 255, 255, 240)   # 亮部高光

MAIN_QSS = f"""
* {{
    font-family: "Segoe UI Variable Display", "Segoe UI", "Microsoft YaHei UI", sans-serif;
    outline: none;
    border: none;
}}

QWidget {{
    background-color: transparent;
    color: {TEXT_PRI_HEX};
}}

/* 滚动条 */
QScrollBar:vertical {{
    border: none;
    background: transparent;
    width: 6px;
    margin: 0px;
}}
QScrollBar::handle:vertical {{
    background: #CBD2DF;
    min-height: 24px;
    border-radius: 3px;
}}
QScrollBar::handle:vertical:hover {{
    background: #A0AEC0;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    background: transparent;
}}

/* 输入框 */
QLineEdit {{
    background-color: #DEE1E8;
    color: {TEXT_PRI_HEX};
    border-radius: 9px;
    padding: 6px 12px;
    font-size: 13px;
    border: 1px solid rgba(174, 174, 192, 0.4);
}}
QLineEdit:focus {{
    border: 1px solid {ACCENT_WORK};
    background-color: #E2E5EC;
}}

/* 拟态卡片按钮基础 */
QPushButton {{
    background-color: {BG_HEX};
    color: {TEXT_PRI_HEX};
    border-radius: 8px;
    font-size: 13px;
    font-weight: 500;
}}
QPushButton:hover {{
    background-color: {BG_HOVER_HEX};
}}
QPushButton:pressed {{
    background-color: {BG_PRESSED_HEX};
}}
"""
