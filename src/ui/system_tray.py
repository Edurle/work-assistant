"""系统托盘模块"""

from PySide6.QtWidgets import QSystemTrayIcon, QMenu
from PySide6.QtGui import QIcon, QAction, QPixmap, QPainter, QColor, QFont
from PySide6.QtCore import Signal, Qt
from loguru import logger
from pathlib import Path


class SystemTrayIcon(QSystemTrayIcon):
    """系统托盘图标"""

    show_window_requested = Signal()
    hide_window_requested = Signal()
    quit_requested = Signal()
    add_reminder_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._create_icon()
        self._create_menu()
        self.setToolTip("Work Assistant - 工作助手")

        # 双击显示窗口
        self.activated.connect(self._on_activated)

        logger.debug("系统托盘初始化完成")

    def _on_activated(self, reason):
        """托盘图标激活事件"""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_window_requested.emit()

    def _create_icon(self):
        """创建托盘图标"""
        # 尝试加载图标文件
        icon_paths = [
            Path(__file__).parent.parent.parent / "resources" / "icons" / "app.png",
            Path(__file__).parent.parent.parent / "resources" / "icons" / "app.ico",
        ]

        for icon_path in icon_paths:
            if icon_path.exists():
                self.setIcon(QIcon(str(icon_path)))
                logger.debug(f"加载托盘图标: {icon_path}")
                return

        # 使用默认图标
        from PySide6.QtGui import QPixmap, QPainter, QColor, QFont
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 绘制圆形背景
        painter.setBrush(QColor("#3498db"))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(4, 4, 56, 56)

        # 绘制文字
        painter.setPen(QColor("white"))
        font = QFont("Arial", 24, QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "W")

        painter.end()

        self.setIcon(QIcon(pixmap))
        logger.debug("使用默认托盘图标")

    def _create_menu(self):
        """创建托盘菜单"""
        menu = QMenu()

        # 显示主窗口
        show_action = QAction("显示主窗口", self)
        show_action.triggered.connect(self.show_window_requested)
        menu.addAction(show_action)

        # 最小化窗口
        hide_action = QAction("最小化窗口", self)
        hide_action.triggered.connect(self.hide_window_requested)
        menu.addAction(hide_action)

        menu.addSeparator()

        # 快速添加提醒
        add_reminder_action = QAction("新建提醒", self)
        add_reminder_action.triggered.connect(self.add_reminder_requested)
        menu.addAction(add_reminder_action)

        menu.addSeparator()

        # 退出
        quit_action = QAction("退出", self)
        quit_action.triggered.connect(self.quit_requested)
        menu.addAction(quit_action)

        self.setContextMenu(menu)

    def show_message(self, title: str, message: str, icon=None, millisecondsTimeoutHint=5000):
        """显示托盘消息"""
        if icon is None:
            icon = QSystemTrayIcon.MessageIcon.Information
        self.showMessage(title, message, icon, millisecondsTimeoutHint)


# 需要导入Qt
from PySide6.QtCore import Qt
