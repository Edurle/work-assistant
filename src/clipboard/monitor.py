"""剪贴板监控模块"""

from PySide6.QtCore import QObject, Signal, QTimer
from PySide6.QtGui import QClipboard, QImage
from PySide6.QtWidgets import QApplication
from loguru import logger
import base64

from .models import ClipboardItem, ContentType


class ClipboardMonitor(QObject):
    """剪贴板监控器"""

    # 信号：检测到新的剪贴板内容
    content_changed = Signal(object)  # ClipboardItem

    def __init__(self, parent=None):
        super().__init__(parent)
        self.clipboard: QClipboard = None
        self.last_hash = ""
        self._is_monitoring = False

        # 防抖：避免短时间内多次触发
        self.debounce_timer = QTimer(self)
        self.debounce_timer.setSingleShot(True)
        self.debounce_timer.timeout.connect(self._check_clipboard)

        logger.debug("剪贴板监控器初始化完成")

    def start_monitoring(self):
        """开始监控"""
        if self._is_monitoring:
            return

        self.clipboard = QApplication.clipboard()
        if self.clipboard:
            self.clipboard.dataChanged.connect(self._on_clipboard_changed)
            self._is_monitoring = True
            logger.info("剪贴板监控已启动")

    def stop_monitoring(self):
        """停止监控"""
        if self._is_monitoring and self.clipboard:
            try:
                self.clipboard.dataChanged.disconnect(self._on_clipboard_changed)
            except RuntimeError:
                pass
            self._is_monitoring = False
            logger.info("剪贴板监控已停止")

    def _on_clipboard_changed(self):
        """剪贴板变化回调（带防抖）"""
        self.debounce_timer.start(100)  # 100ms防抖

    def _check_clipboard(self):
        """检查剪贴板内容"""
        if not self.clipboard:
            return

        mime_data = self.clipboard.mimeData()
        if not mime_data:
            return

        try:
            # 检测内容类型并提取
            if mime_data.hasImage():
                content_type = ContentType.IMAGE
                image = self.clipboard.image()
                if image.isNull():
                    return
                content = self._image_to_base64(image)
                preview = f"[图片 {image.width()}x{image.height()}]"
            elif mime_data.hasHtml():
                content_type = ContentType.HTML
                content = mime_data.html()
                preview = self._extract_text_preview(content)
            elif mime_data.hasText():
                content_type = ContentType.TEXT
                content = mime_data.text()
                preview = self._extract_text_preview(content)
            else:
                return

            # 计算哈希，去重
            content_hash = ClipboardItem.generate_hash(content, content_type)
            if content_hash == self.last_hash:
                return
            self.last_hash = content_hash

            # 创建剪贴板项并发送信号
            item = ClipboardItem(
                content=content,
                content_type=content_type,
                preview=preview,
                hash=content_hash,
            )

            logger.debug(f"检测到新剪贴板内容: {content_type.value}, 预览: {preview[:50]}")
            self.content_changed.emit(item)

        except Exception as e:
            logger.error(f"处理剪贴板内容时出错: {e}")

    @staticmethod
    def _extract_text_preview(text: str, max_length: int = 100) -> str:
        """提取文本预览"""
        preview = text.replace('\n', ' ').replace('\r', ' ').strip()
        if len(preview) > max_length:
            preview = preview[:max_length] + "..."
        return preview

    @staticmethod
    def _image_to_base64(image: QImage) -> str:
        """图片转Base64"""
        from io import BytesIO
        buffer = BytesIO()

        # 转换为PNG格式
        if image.format() != QImage.Format.Format_ARGB32:
            image = image.convertToFormat(QImage.Format.Format_ARGB32)

        image.save(buffer, "PNG")
        return base64.b64encode(buffer.getvalue()).decode('utf-8')

    def is_monitoring(self) -> bool:
        """返回监控状态"""
        return self._is_monitoring
