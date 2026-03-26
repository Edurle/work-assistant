# Work Assistant - 工作助手

一个跨平台的Python桌面应用，提供剪贴板管理和定时提醒功能。

## 功能特性

### 剪贴板管理
- 📋 无限剪贴板历史记录
- 🏷️ 自动分类（代码、链接、图片、文本）
- ⭐ 收藏重要内容
- 🔍 快速搜索
- 🗂️ 自定义分类

### 定时提醒
- ⏰ 时间点提醒
- 🔄 间隔提醒（秒/分钟/小时/天）
- 🔔 系统通知 + 弹窗
- 😴 贪睡功能

### 跨平台
- ✅ Windows 支持
- ✅ Ubuntu/Linux 支持
- 🖥️ 系统托盘集成

## 安装

### 方法一：使用 Conda（推荐）

```bash
# 创建conda环境
conda create -n work-assistant python=3.11 -y

# 激活环境
conda activate work-assistant

# 安装依赖
pip install PySide6 loguru plyer notify2 Pillow

# 运行应用
cd /home/wang/work-assistant
python src/main.py
```

### 方法二：使用启动脚本

```bash
# 直接运行启动脚本
./run.sh
```

### 方法三：系统Python

```bash
# 安装依赖
pip install -r requirements.txt

# 运行应用
python src/main.py
```

## 使用说明

### 剪贴板
1. 应用启动后自动监控剪贴板
2. 复制的内容会自动保存并分类
3. 双击列表项复制到剪贴板
4. 右键可收藏、移动分类、删除

### 提醒
1. 点击"新建提醒"创建提醒
2. 选择时间点或间隔模式
3. 到达时间后弹出通知
4. 可贪睡5分钟

## 项目结构

```
work-assistant/
├── src/
│   ├── main.py              # 入口
│   ├── app.py               # 主应用类
│   ├── core/
│   │   ├── database.py      # 数据库管理
│   │   └── config.py        # 配置管理
│   ├── clipboard/
│   │   ├── monitor.py       # 剪贴板监控
│   │   ├── manager.py       # 剪贴板管理
│   │   └── models.py        # 数据模型
│   ├── reminder/
│   │   ├── scheduler.py     # 提醒调度
│   │   ├── notification.py  # 通知处理
│   │   └── models.py        # 数据模型
│   └── ui/
│       ├── main_window.py   # 主窗口
│       ├── system_tray.py   # 系统托盘
│       ├── clipboard_panel.py
│       └── reminder_panel.py
├── resources/
│   └── icons/               # 图标资源
├── requirements.txt
└── README.md
```

## 数据存储

- **数据库**: `~/.local/share/work-assistant/data/work_assistant.db`
- **配置**: `~/.config/work-assistant/config.json`
- **日志**: `~/.local/share/work-assistant/logs/`

Windows下存储在 `%APPDATA%/work-assistant/`

## 开发

### 安装开发依赖

```bash
pip install -r requirements-dev.txt
```

### 运行测试

```bash
pytest tests/
```

### 打包

```bash
# 使用 PyInstaller
pyinstaller --name "Work Assistant" --windowed src/main.py
```

## 技术栈

- **GUI框架**: PySide6 (Qt6)
- **数据库**: SQLite
- **通知**: plyer + notify2
- **日志**: loguru

## 许可证

MIT License
# work-assistant
