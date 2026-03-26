"""主窗口模块"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QSplitter, QStatusBar, QToolBar
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QIcon
from loguru import logger
from pathlib import Path

from src.ui.clipboard_panel import ClipboardPanel
from src.ui.reminder_panel import ReminderPanel


class MainWindow(QMainWindow):
    """主窗口"""

    def __init__(self, config, clipboard_manager, reminder_scheduler, parent=None):
        super().__init__(parent)
        self.config = config
        self.clipboard_manager = clipboard_manager
        self.reminder_scheduler = reminder_scheduler

        self._init_ui()
        self._restore_geometry()
        self._create_toolbar()

        logger.debug("主窗口初始化完成")

    def _init_ui(self):
        """初始化UI"""
        self.setWindowTitle("Work Assistant - 工作助手")
        self.setMinimumSize(800, 600)

        # 中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # 标签页
        self.tab_widget = QTabWidget()
        self.tab_widget.setDocumentMode(True)

        # 剪贴板面板
        self.clipboard_panel = ClipboardPanel(self.clipboard_manager)
        self.tab_widget.addTab(self.clipboard_panel, "📋 剪贴板")

        # 提醒面板
        self.reminder_panel = ReminderPanel(self.reminder_scheduler)
        self.tab_widget.addTab(self.reminder_panel, "⏰ 提醒")

        main_layout.addWidget(self.tab_widget)

        # 状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪")

    def _create_toolbar(self):
        """创建工具栏"""
        toolbar = QToolBar("主工具栏")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        # 刷新
        refresh_action = QAction("刷新", self)
        refresh_action.setToolTip("刷新当前面板")
        refresh_action.triggered.connect(self._refresh_current_panel)
        toolbar.addAction(refresh_action)

        toolbar.addSeparator()

        # 设置
        settings_action = QAction("设置", self)
        settings_action.setToolTip("打开设置")
        settings_action.triggered.connect(self._open_settings)
        toolbar.addAction(settings_action)

        toolbar.addSeparator()

        # 关于
        about_action = QAction("关于", self)
        about_action.setToolTip("关于 Work Assistant")
        about_action.triggered.connect(self._show_about)
        toolbar.addAction(about_action)

        toolbar.addSeparator()

        # 退出
        quit_action = QAction("退出", self)
        quit_action.setToolTip("退出应用")
        quit_action.triggered.connect(self._quit_app)
        toolbar.addAction(quit_action)

    def _restore_geometry(self):
        """恢复窗口几何信息"""
        cfg = self.config.data
        self.resize(cfg.window_width, cfg.window_height)

        if cfg.window_x is not None and cfg.window_y is not None:
            self.move(cfg.window_x, cfg.window_y)

    def _save_geometry(self):
        """保存窗口几何信息"""
        self.config.set('window_width', self.width())
        self.config.set('window_height', self.height())
        self.config.set('window_x', self.x())
        self.config.set('window_y', self.y())

    def _refresh_current_panel(self):
        """刷新当前面板"""
        current = self.tab_widget.currentWidget()
        if hasattr(current, '_load_items'):
            current._load_items()
        elif hasattr(current, '_load_reminders'):
            current._load_reminders()
        self.status_bar.showMessage("已刷新", 2000)

    def _open_settings(self):
        """打开设置"""
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.information(self, "设置", "设置功能开发中...")

    def _show_about(self):
        """显示关于"""
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.about(
            self,
            "关于 Work Assistant",
            """<h2>Work Assistant</h2>
            <p>版本 1.0.0</p>
            <p>一个跨平台的工作助手应用</p>
            <p>功能：</p>
            <ul>
            <li>剪贴板历史管理</li>
            <li>定时提醒</li>
            <li>分类归档</li>
            </ul>
            """
        )

    def _quit_app(self):
        """直接退出应用"""
        self._save_geometry()
        if hasattr(self, '_quit_callback') and self._quit_callback:
            self._quit_callback()
        logger.debug("用户选择直接退出应用")

    def closeEvent(self, event):
        """关闭事件 - 最小化到托盘"""
        # 保存窗口几何信息
        self._save_geometry()

        # 隐藏窗口（最小化到托盘）而不是退出
        event.ignore()
        self.hide()
        logger.debug("窗口最小化到托盘")

    def set_quit_callback(self, callback):
        """设置退出回调"""
        self._quit_callback = callback

    def show_and_activate(self):
        """显示并激活窗口"""
        self.show()
        self.raise_()
        self.activateWindow()

    def get_clipboard_panel(self) -> ClipboardPanel:
        """获取剪贴板面板"""
        return self.clipboard_panel

    def get_reminder_panel(self) -> ReminderPanel:
        """获取提醒面板"""
        return self.reminder_panel
