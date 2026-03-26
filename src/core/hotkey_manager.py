"""全局快捷键管理模块"""

from PySide6.QtCore import QObject, Signal
from pynput import keyboard as kb
from loguru import logger


class HotkeyManager(QObject):
    """全局快捷键管理器"""

    alt_v_triggered = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._listener = None
        self._running = False

    def start(self):
        """启动快捷键监听"""
        if self._running:
            return

        try:
            self._listener = kb.GlobalHotKeys({
                '<alt>+v': self._on_alt_v
            })
            self._listener.start()
            self._running = True
            logger.info("全局快捷键监听已启动 (Alt+V)")
        except Exception as e:
            logger.error(f"启动快捷键监听失败: {e}")

    def stop(self):
        """停止快捷键监听"""
        if self._listener and self._running:
            try:
                self._listener.stop()
                self._running = False
                logger.info("全局快捷键监听已停止")
            except Exception as e:
                logger.error(f"停止快捷键监听失败: {e}")

    def _on_alt_v(self):
        """Alt+V 触发回调"""
        logger.debug("快捷键 Alt+V 触发")
        self.alt_v_triggered.emit()
