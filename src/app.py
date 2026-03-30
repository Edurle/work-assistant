"""主应用模块"""

from PySide6.QtCore import QObject, Slot
from PySide6.QtWidgets import QApplication
from loguru import logger
import sys

from src.core.database import Database
from src.core.config import Config
from src.core.hotkey_manager import HotkeyManager
from src.clipboard.monitor import ClipboardMonitor
from src.clipboard.manager import ClipboardManager
from src.reminder.scheduler import ReminderScheduler
from src.reminder.notification import NotificationManager
from src.ui.main_window import MainWindow
from src.ui.system_tray import SystemTrayIcon
from src.ui.quick_paste_popup import QuickPastePopup


class WorkAssistantApp(QObject):
    """主应用类"""

    def __init__(self, argv=None):
        super().__init__()

        # 创建QApplication
        self.app = QApplication(argv if argv else sys.argv)
        self.app.setApplicationName("Work Assistant")
        self.app.setApplicationVersion("1.0.0")
        self.app.setQuitOnLastWindowClosed(False)

        # 初始化核心组件
        self.db = Database()
        self.config = Config()

        # 初始化模块
        self.clipboard_monitor = ClipboardMonitor(self)
        self.clipboard_manager = ClipboardManager(self.db)
        self.reminder_scheduler = ReminderScheduler(self.db, self)
        self.notification_manager = NotificationManager()

        # 初始化快捷键和快速粘贴
        if self.config.data.quick_paste_enabled:
            self.hotkey_manager = HotkeyManager(self)
            self.quick_paste_popup = QuickPastePopup(self.clipboard_manager, None)
        else:
            self.hotkey_manager = None
            self.quick_paste_popup = None

        # 初始化UI
        self.main_window = MainWindow(
            self.config,
            self.clipboard_manager,
            self.reminder_scheduler
        )
        self.main_window.set_quit_callback(self.quit)

        # 初始化托盘
        self.system_tray = SystemTrayIcon()
        self.notification_manager.set_tray_icon(self.system_tray)

        # 连接信号
        self._connect_signals()

        logger.info("Work Assistant 初始化完成")

    def _connect_signals(self):
        """连接信号和槽"""
        # 剪贴板监控 -> 保存
        self.clipboard_monitor.content_changed.connect(
            self._on_clipboard_changed
        )

        # 提醒触发 -> 通知
        self.reminder_scheduler.reminder_triggered.connect(
            self._on_reminder_triggered
        )

        # 系统托盘
        self.system_tray.show_window_requested.connect(
            self._show_main_window
        )
        self.system_tray.hide_window_requested.connect(
            self.main_window.hide
        )
        self.system_tray.quit_requested.connect(
            self.quit
        )
        self.system_tray.add_reminder_requested.connect(
            self._show_add_reminder
        )

        # 快捷键
        if self.hotkey_manager:
            self.hotkey_manager.alt_v_triggered.connect(
                self._show_quick_paste
            )

    @Slot(object)
    def _on_clipboard_changed(self, item):
        """处理剪贴板变化"""
        item_id = self.clipboard_manager.save_item(item)
        if item_id:
            self.main_window.get_clipboard_panel().add_item(item)

    @Slot(object)
    def _on_reminder_triggered(self, reminder):
        """处理提醒触发"""
        logger.info(f"提醒触发: {reminder.title}")

        # 只显示正中央弹窗，不显示右下角系统通知
        result = self.notification_manager.show_popup_dialog(reminder)
        if result == 2:
            self.reminder_scheduler.snooze_reminder(reminder.id, minutes=5)

        self.main_window.get_reminder_panel()._load_reminders()

    @Slot()
    def _show_main_window(self):
        """显示主窗口"""
        self.main_window.show_and_activate()

    @Slot()
    def _show_add_reminder(self):
        """显示添加提醒"""
        self._show_main_window()
        self.main_window.get_reminder_panel()._add_reminder()

    def run(self):
        """运行应用"""
        self.clipboard_monitor.start_monitoring()
        self.reminder_scheduler.start()
        if self.hotkey_manager:
            self.hotkey_manager.start()
        self.system_tray.show()

        if not self.config.data.start_minimized:
            self.main_window.show()

        logger.info("应用启动")
        return self.app.exec()

    def quit(self):
        """退出应用"""
        logger.info("正在退出应用...")
        if self.hotkey_manager:
            self.hotkey_manager.stop()
        self.clipboard_monitor.stop_monitoring()
        self.reminder_scheduler.stop()
        self.config.save()
        self.app.quit()

    @Slot()
    def _show_quick_paste(self):
        """显示快速粘贴弹窗"""
        if self.quick_paste_popup:
            self.quick_paste_popup.show_popup()
