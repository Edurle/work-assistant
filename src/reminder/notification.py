"""跨平台通知模块"""

from PySide6.QtCore import QObject, Qt, QTimer
from PySide6.QtWidgets import QSystemTrayIcon, QMessageBox, QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
from PySide6.QtGui import QIcon
from typing import Optional
from loguru import logger
import platform
import subprocess


class NotificationDialog(QDialog):
    """提醒弹窗对话框"""

    def __init__(self, reminder, parent=None, auto_close_seconds: int = 3):
        super().__init__(parent)
        self.reminder = reminder
        self.auto_close_seconds = auto_close_seconds
        self._auto_close_timer = QTimer(self)
        self._auto_close_timer.setSingleShot(True)
        self._auto_close_timer.timeout.connect(self.accept)
        self._init_ui()

    def _init_ui(self):
        """初始化UI"""
        self.setWindowTitle("提醒 - " + self.reminder.title)
        self.setMinimumWidth(400)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)

        layout = QVBoxLayout(self)

        # 标题
        title_label = QLabel(f"<h2>{self.reminder.title}</h2>")
        layout.addWidget(title_label)

        # 内容
        if self.reminder.content:
            content_label = QLabel(self.reminder.content)
            content_label.setWordWrap(True)
            layout.addWidget(content_label)

        # 按钮
        button_layout = QHBoxLayout()

        if self.reminder.reminder_type.value == 'interval':
            snooze_btn = QPushButton("贪睡 5 分钟")
            snooze_btn.clicked.connect(self._snooze)
            button_layout.addWidget(snooze_btn)

        ok_btn = QPushButton("确定")
        ok_btn.clicked.connect(self.accept)
        ok_btn.setDefault(True)
        button_layout.addWidget(ok_btn)

        layout.addLayout(button_layout)

    def _snooze(self):
        """贪睡"""
        self._cancel_auto_close()
        self.done(2)  # 2 表示贪睡

    def _cancel_auto_close(self):
        """取消自动关闭"""
        if self._auto_close_timer.isActive():
            self._auto_close_timer.stop()

    def exec(self):
        """执行对话框，启动自动关闭定时器"""
        self._auto_close_timer.start(self.auto_close_seconds * 1000)
        return super().exec()

    def accept(self):
        """确定按钮点击"""
        self._cancel_auto_close()
        super().accept()

    def reject(self):
        """关闭对话框"""
        self._cancel_auto_close()
        super().reject()


class NotificationManager(QObject):
    """跨平台通知管理器"""

    def __init__(self, tray_icon: Optional[QSystemTrayIcon] = None, parent=None):
        super().__init__(parent)
        self.tray_icon = tray_icon
        self.system = platform.system()
        self._init_platform_notification()
        logger.debug(f"通知管理器初始化完成，平台: {self.system}")

    def _init_platform_notification(self):
        """初始化平台特定的通知"""
        self.notify2 = None
        self.plyer = None

        if self.system == "Linux":
            try:
                import notify2
                notify2.init("Work Assistant")
                self.notify2 = notify2
                logger.debug("Linux notify2 初始化成功")
            except ImportError:
                logger.warning("notify2 未安装，将使用备选通知方式")
        elif self.system == "Windows":
            try:
                from plyer import notification
                self.plyer = notification
                logger.debug("Windows plyer 初始化成功")
            except ImportError:
                logger.warning("plyer 未安装，将使用备选通知方式")

    def show_notification(self, title: str, message: str,
                          timeout: int = 5000,
                          sound: bool = True):
        """显示通知"""
        logger.debug(f"显示通知: {title}")

        # 方案1：使用系统托盘通知（跨平台备选）
        if self.tray_icon:
            try:
                self.tray_icon.showMessage(
                    title,
                    message,
                    QSystemTrayIcon.MessageIcon.Information,
                    timeout
                )
            except Exception as e:
                logger.warning(f"托盘通知失败: {e}")

        # 方案2：使用平台原生通知
        if self.system == "Linux" and self.notify2:
            self._show_linux_notification(title, message, timeout)
        elif self.system == "Windows" and self.plyer:
            self._show_windows_notification(title, message, timeout)

        # 播放声音
        if sound:
            self._play_sound()

    def _show_linux_notification(self, title: str, message: str, timeout: int):
        """Linux通知"""
        try:
            n = self.notify2.Notification(title, message)
            n.set_timeout(timeout)
            n.show()
            logger.debug("Linux通知发送成功")
        except Exception as e:
            logger.warning(f"Linux通知发送失败: {e}")

    def _show_windows_notification(self, title: str, message: str, timeout: int):
        """Windows通知"""
        try:
            self.plyer.notify(
                title=title,
                message=message,
                app_name="Work Assistant",
                timeout=timeout // 1000
            )
            logger.debug("Windows通知发送成功")
        except Exception as e:
            logger.warning(f"Windows通知发送失败: {e}")

    def _play_sound(self):
        """播放提示音"""
        try:
            if self.system == "Windows":
                import winsound
                winsound.MessageBeep()
            else:  # Linux
                # 尝试播放系统提示音
                subprocess.run(
                    ['aplay', '-q', '/usr/share/sounds/freedesktop/stereo/message.oga'],
                    capture_output=True,
                    timeout=5
                )
        except Exception:
            pass  # 静默失败

    def show_popup_dialog(self, reminder, parent=None) -> int:
        """显示弹窗对话框

        Returns:
            1: 确定
            2: 贪睡
            0: 关闭
        """
        from PySide6.QtCore import Qt

        dialog = NotificationDialog(reminder, parent)
        dialog.setWindowFlags(dialog.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        result = dialog.exec()
        return result

    def set_tray_icon(self, tray_icon: QSystemTrayIcon):
        """设置系统托盘图标"""
        self.tray_icon = tray_icon
