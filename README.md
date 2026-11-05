# FloaTodo 🍅

> 悬浮窗口式待办清单 · Windows 桌面应用

---

## 项目概述

一个始终置顶的轻量级浮动窗口应用，集成实时时钟、番茄工作法计时器和任务管理功能。  
采用 **新拟态（Neumorphism）** 设计风格，界面美观、动画流畅。

---

## 技术方案

| 层次 | 技术 | 说明 |
|------|------|------|
| UI 渲染 | **pywebview 6.2.1 + WebView2** | 用系统 Edge 渲染 HTML，1:1 还原设计稿 |
| 前端 | **HTML / CSS / JavaScript** | 单文件内联，新拟态 CSS 变量体系 |
| Python 后端 | **Python 3.13** | 时钟、番茄钟、任务管理业务逻辑 |
| JS↔Python 通信 | **HTTP 命令服务器** | `fetch()` → Python `http.server`（绕过 pywebview API bridge 兼容性问题） |
| Python→JS 推送 | **`evaluate_js()`** | 时钟、番茄钟状态实时推送 |
| 数据持久化 | **SQLite 3**（WAL 模式） | 任务数据，轻量无依赖 |
| 窗口控制 | **Win32 API（ctypes）** | 圆角窗口、关闭、拖拽移动 |

### 为什么不用 PySide6 / PyQt6？

在目标 Windows 10 环境（10.0.19045）中，PySide6 / PyQt6 的 Qt6 DLL 存在系统依赖版本不兼容问题（Error 127），两种框架均无法加载。最终改用 pywebview + WebView2（系统已内置 Edge），稳定运行，内存占用约 50–80 MB。

---

## 功能清单

### ✅ 已实现

| 功能 | 状态 | 说明 |
|------|------|------|
| 实时时钟 | ✅ | 秒级更新，冒号闪烁动画 |
| 番茄钟 | ✅ | IDLE→WORK→SHORT→LONG 状态机，可配置时长 |
| 任务增删 | ✅ | SQLite 持久化，重启数据保留 |
| 任务完成 | ✅ | 勾选 / 取消，删除线动画 |
| 任务计时 | ✅ | 每个任务独立累计计时 |
| 右键删除 | ✅ | 右键菜单删除任务 |
| 置顶悬浮 | ✅ | always-on-top，无边框圆角窗口 |
| 拖拽移动 | ✅ | 点击标题栏拖动 |
| 关闭保存位置 | ✅ | 重启后恢复窗口位置 |
| 迷你模式（⊟） | ⚠️ | CSS 生效，窗口缩放部分工作，见已知问题 |
| 最小化（—） | ✅ | WM_SYSCOMMAND SC_MINIMIZE 进任务栏 |
| 完成涟漪动画 | ✅ | 番茄完成后圆环扩散特效 |
| 新拟态 UI | ✅ | 双侧高斯模糊阴影，与设计稿一致 |

### ❌ 未实现 / 待开发

- 系统托盘图标（Tray Icon）
- 任务编辑（双击修改标题）
- 番茄钟自定义时长（设置面板）
- 任务排序 / 拖拽调整顺序
- 数据统计 / 历史记录
- 通知（番茄完成系统提醒）

---

## 已知问题

### 🔴 高优先级

| 问题 | 现象 | 分析 |
|------|------|------|
| **迷你模式窗口缩放不稳定** | CSS mini 样式生效，但 125×125 实际缩放效果不一致；圆环有时仅显示底部弧线 | `FindWindowW("FloaTodo")` 有时找不到 pywebview 创建的 HWND；pywebview 内置 `window.resize()` 和 Win32 `SetWindowPos` 均尝试但行为不完全一致 |
| **迷你模式退出方式** | ⤡ 按钮可能因宽度被截断不可见 | 已添加"点击圆环退出"和"双击标题栏退出"作为备用 |

### 🟡 中优先级

| 问题 | 现象 | 解决方案 |
|------|------|------|
| pywebview API bridge 失效 | `window.pywebview.api.*` 在 file:// 协议下不工作 | 已改用本地 HTTP 命令服务器 + `fetch()` 绕过 |
| HWND 查找困难 | `EnumWindows` 有时找不到 pywebview 窗口 | 已实现 4 种备选查找方式 + 移至 `on_page_loaded` 后查找 |

### 🟢 已修复

- ~~日期在周三/周四之间乱跳~~ → ClockCore 添加重入保护
- ~~关闭按钮无响应~~ → 改用 `os._exit(0)` + HTTP 命令服务器
- ~~所有标题栏按钮无效~~ → 移除 `pywebview-drag-region` class + `e.preventDefault()`
- ~~迷你模式 CSS 不生效~~ → 修复 `.body.mini` 拼写错误为 `body.mini`
- ~~关闭后窗口不可见~~ → 迷你模式下不保存窗口坐标

---

## 项目结构

```
floatodo/
├── main.py              # pywebview 入口，HTTP 命令服务器启动
├── api.py               # Python↔JS 桥接层（HTTP handler + evaluate_js 推送）
├── requirements.txt     # 依赖声明
│
├── core/                # 纯 Python 业务逻辑（无 UI 依赖）
│   ├── clock.py         # 实时时钟（后台线程，Signal 驱动）
│   ├── pomodoro.py      # 番茄钟状态机
│   ├── task_manager.py  # 任务 CRUD（SQLite 后端）
│   ├── task_timer.py    # 任务计时器
│   ├── models.py        # 数据模型（Task, PomodoroPhase 等）
│   └── signal.py        # 轻量级信号/回调系统（替代 Qt Signal）
│
├── ui/
│   └── index.html       # 完整前端（HTML + CSS + JS，单文件内联）
│
├── config/
│   └── settings.py      # 配置读写（JSON 后端）
│
└── utils/
    └── db.py            # SQLite 连接单例（WAL 模式）
```

---

## 安装与运行

```bash
# 克隆项目
git clone <repo-url>
cd floatodo

# 安装依赖（需要 Python 3.11+ 和 Microsoft Edge）
pip install -r requirements.txt

# 运行
python main.py
```

### 依赖

```
pywebview>=6.2.0    # WebView2 渲染（需要系统已安装 Edge）
pywin32>=306        # Win32 API（窗口控制）
keyboard>=0.13.5    # 全局热键（Ctrl+Shift+F 恢复隐藏窗口）
winotify>=1.1.0     # Windows Toast 通知（备用）
```

---

## UI 设计规格

**风格**：新拟态（Neumorphism）浅色系

| Token | 值 | 用途 |
|-------|----|------|
| `--bg` | `#E8EAF0` | 基础背景色 |
| `--sd` | `rgba(174,174,192,.42)` | 暗侧阴影 |
| `--sl` | `rgba(255,255,255,.95)` | 亮侧高光 |
| `--phase-work` | `#7C6EBE` | 专注阶段（紫） |
| `--phase-short` | `#68B495` | 短休阶段（绿） |
| `--phase-long` | `#6BA3D6` | 长休阶段（蓝） |
| `--amber` | `#E6A817` | 任务计时激活色 |

**字体**：Segoe UI（UI 文字）+ Consolas（时钟 / 倒计时数字）

**窗口**：320×640px，圆角 20px（Win32 SetWindowRgn），始终置顶，无系统边框

---

## 开发记录（关键决策）

### 2026-11-05

**通信架构**：最初用 pywebview 的 `window.pywebview.api.*` JS→Python 通信，发现在此 Windows 10 环境下 WebView2 的 host object 无响应（消息通道无法建立）。改为本地 HTTP 命令服务器方案——Python 启动 `http.server` 监听随机端口，页面加载后通过 `evaluate_js` 注入端口号，之后所有 JS→Python 调用走 `fetch(POST)` 实现。该方案完全绕开 pywebview API bridge，稳定可靠。

**tkinter → pywebview**：初版用 tkinter + Pillow 实现新拟态 UI，但字体渲染、emoji 显色、圆角窗口等效果与 HTML 预览差距较大。改用 pywebview 后 UI 与设计稿完全一致（浏览器级渲染质量）。

**HWND 获取**：pywebview 创建的 Win32 窗口通过标准 `EnumWindows` 有时找不到（可能是 CLR STA 线程问题）。将 HWND 查找从 `on_shown` 移至 `on_page_loaded`（`<title>FloaTodo</title>` 生效后），并增加 4 种备选方式（FindWindowW / GetForegroundWindow / EnumWindows 标题 / EnumWindows 尺寸+TOPMOST）。
