# FloaTodo 🍅

> Windows 悬浮窗口番茄钟 · 待办清单 · 原生 PySide6

---

## 项目概述

始终置顶的轻量级浮动窗口应用，将 **Windows 专注风格表盘** 与 **待办清单** 融为一体。  
采用 **新拟态（Neumorphism）** 浅色系设计，纯 Python + PySide6 原生渲染，零浏览器依赖，内存占用约 30 MB。

---

## 技术栈

| 层次 | 技术 | 说明 |
|------|------|------|
| **UI 引擎** | PySide6 (Qt 6.5+) | 硬件加速抗锯齿渲染，拖拽/缩放零延迟 |
| **视觉风格** | Neumorphism + Windows Focus Dial | 30 刻度环形表盘，动态流光胶囊进度点，MM:SS 居中大字 |
| **音效系统** | winsound + QtMultimedia（可选） | 系统默认音 + 自定义音频导入，超时自动卡断 |
| **数据持久化** | SQLite 3（WAL 模式）+ JSON | 任务数据与偏好设置即时本地存储，重启继承 |
| **系统集成** | Win32 DWM · Qt Tray · keyboard | 毛玻璃 DWM 模糊、系统托盘常驻、全局热键 `Ctrl+Shift+F` |

---

## 功能清单

| 功能 | 交互方式 |
|------|---------|
| **环形专注表盘** | 30 刻度，中心 MM:SS 倒计时，完成时光环波纹动效 |
| **番茄钟状态机** | IDLE → WORK → SHORT_BREAK → LONG_BREAK，支持跳过、重置 |
| **大满贯番茄** | 完成 N 轮（默认 4）自动收获 🍅×1，持久化累计 |
| **待办增删** | 顶部「＋ 添加」栏，输入回车即添加，自动更新 TODAY (n/m) |
| **待办拖拽排序** | 拖住左侧 ⠿ 手柄上下拖拽，紫色指示线实时预览，松手持久化 |
| **右键编辑任务** | 右键 → ✏️ 编辑任务名称，原地内联 QLineEdit，Enter 或失焦保存 |
| **右键删除任务** | 右键 → 🗑 删除任务 |
| **任务勾选完成** | 点击复选框，标题划线 + TODAY 计数实时更新 |
| **任务独立秒表** | 每任务卡片 ⏱ 按钮，计时累计并持久化 |
| **边缘拖拽缩放** | 窗口 8 方向边缘 7px 热区，系统原生缩放，遵守 min/max 约束 |
| **迷你模式 ⊟** | 切换至 148×185 极简悬浮挂件，始终仅显示倒计时 |
| **毛玻璃皮肤 ❄** | DWM BlurBehind + 半透明卡片，迷你/完整模式均生效 |
| **偏好设置** | 自定义轮数、专注/短休/长休时长、音效开关与文件导入 |
| **窗口置顶 📌** | 带旋转动效图钉，状态持久化 |
| **窗口拖动** | 拖拽标题栏，位置保存至下次启动 |
| **系统托盘** | 🍅 托盘图标，左键/双击显隐窗口 |
| **全局热键** | `Ctrl+Shift+F` 随时召回/隐藏，后台线程注册，不阻塞 UI |
| **阶段通知** | 系统 Tray 气泡 + 音效提示，可自定义音频 |

---

## 项目结构

```
floatodo/
├── main.py              # 应用主入口（conda DLL 路径修复 + 启动 PySide6）
├── main_qt.py           # PySide6 主程序（QApplication 初始化、热键线程）
├── requirements.txt     # 依赖：PySide6, keyboard, pywin32
├── build_exe.py         # PyInstaller 打包脚本（生成独立便携 EXE）
├── FloaTodo.spec        # PyInstaller Spec
├── app.ico              # 应用图标
│
├── ui_qt/               # 原生 Qt UI 层
│   ├── main_window.py   # 主窗体（布局、番茄调度、托盘、缩放过滤器）
│   ├── focus_dial.py    # 专注表盘（QPainter 刻度环、波纹动效）
│   ├── task_widget.py   # 任务列表（拖拽排序、内联编辑、条目组件）
│   ├── title_bar.py     # 无边框标题栏（置顶、迷你、毛玻璃、拖动）
│   ├── controls.py      # 矢量圆形按钮、图钉旋转动画
│   ├── settings_dialog.py  # 偏好设置面板
│   ├── sound_manager.py    # 音效管理（系统音 + 自定义文件 + 卡断）
│   ├── window_effects.py   # Win32 DWM 毛玻璃（SetWindowCompositionAttribute）
│   └── styles.py           # 新拟态配色系统与全局 QSS
│
├── core/                # 纯 Python 业务逻辑（无 Qt 依赖）
│   ├── pomodoro.py      # 番茄钟状态机
│   ├── task_manager.py  # 任务 CRUD（SQLite 驱动）
│   ├── task_timer.py    # 任务秒表计时器
│   ├── models.py        # 数据模型（Task, PomodoroPhase, Priority）
│   └── signal.py        # 轻量观察者 Signal（connect / emit）
│
├── config/
│   └── settings.py      # JSON 配置读写，记忆窗口位置与偏好
│
├── utils/
│   └── db.py            # SQLite 单例连接（WAL 模式）
│
├── data/                # 运行时数据（git-ignored）
│   ├── tasks.db         # 任务数据库
│   └── settings.json    # 用户配置
│
└── sound/               # 内置提示音样例
```

---

## 安装与运行

### 方式一：便携 EXE（推荐）

```
dist/FloaTodo.exe
```

无需 Python，双击即用。`data/` 目录与 EXE 同级，可随身携带。

### 方式二：源码运行

```bash
pip install -r requirements.txt
python main.py
```

> **conda 环境说明**：conda 编译的 PySide6 与 pip 安装的 Qt DLL 存在版本冲突。  
> 推荐使用 `conda install pyside6`，然后直接 `python main.py`，  
> 入口已内置 `Library/bin` DLL 路径自动修复（非 venv 环境下生效）。

### 方式三：重新打包 EXE

```bash
python build_exe.py
```

---

## 关键设计说明

### 毛玻璃（❄）实现原理

Qt 窗口设置 `WA_TranslucentBackground=True` 后，内部使用 `UpdateLayeredWindowIndirect` 管理透明。  
`SetLayeredWindowAttributes(LWA_ALPHA)` 与前者**互斥**，调用后每帧都会报错。  
本项目只调用 `SetWindowCompositionAttribute`（DWM BlurBehind），实际透明度由卡片 CSS `rgba()` 控制，三者互不干扰。

### 边缘缩放实现原理

通过应用级 `QObject.eventFilter` 检测鼠标在窗口边缘 7px 热区，  
调用 `QWindow.startSystemResize()` 将缩放完全委托给操作系统，  
无需 Win32 `WM_NCHITTEST` ctypes 结构，不干扰 Qt 内部鼠标事件路由。

### 热键线程安全

`keyboard.add_hotkey()` 在 `app.exec()` 之前调用会阻塞主线程。  
本项目将热键注册放入 Daemon 线程，回调通过 `QMetaObject.invokeMethod(..., QueuedConnection)` 转发到主线程执行。

---

## 依赖

```
PySide6>=6.5.0    # Qt 原生 UI
keyboard>=0.13.5  # 全局热键（需管理员权限或无障碍权限）
pywin32>=306      # Win32 DWM API 访问
```
