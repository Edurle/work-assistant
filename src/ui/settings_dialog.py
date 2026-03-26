"""设置对话框模块"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QSpinBox, QSlider, QDialogButtonBox, QGroupBox
)
from PySide6.QtCore import Qt
from loguru import logger


class SettingsDialog(QDialog):
    """设置对话框"""

    MIN_FONT_SIZE = 8
    MAX_FONT_SIZE = 24

    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self._init_ui()
        self._load_settings()

    def _init_ui(self):
        """初始化UI"""
        self.setWindowTitle("设置")
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)

        # 剪贴板面板字体设置
        clipboard_group = QGroupBox("剪贴板面板字体")
        clipboard_layout = QVBoxLayout(clipboard_group)

        # 字体大小控制行
        clipboard_row = QHBoxLayout()
        clipboard_row.addWidget(QLabel("字体大小:"))

        self.clipboard_spinbox = QSpinBox()
        self.clipboard_spinbox.setRange(self.MIN_FONT_SIZE, self.MAX_FONT_SIZE)
        self.clipboard_spinbox.setSuffix(" pt")
        clipboard_row.addWidget(self.clipboard_spinbox)

        self.clipboard_slider = QSlider(Qt.Orientation.Horizontal)
        self.clipboard_slider.setRange(self.MIN_FONT_SIZE, self.MAX_FONT_SIZE)
        self.clipboard_slider.setMaximumWidth(200)
        clipboard_row.addWidget(self.clipboard_slider)

        clipboard_layout.addLayout(clipboard_row)

        # 预览
        self.clipboard_preview = QLabel("预览: 这是剪贴板内容的预览文本")
        clipboard_layout.addWidget(self.clipboard_preview)

        layout.addWidget(clipboard_group)

        # 提醒面板字体设置
        reminder_group = QGroupBox("提醒面板字体")
        reminder_layout = QVBoxLayout(reminder_group)

        # 字体大小控制行
        reminder_row = QHBoxLayout()
        reminder_row.addWidget(QLabel("字体大小:"))

        self.reminder_spinbox = QSpinBox()
        self.reminder_spinbox.setRange(self.MIN_FONT_SIZE, self.MAX_FONT_SIZE)
        self.reminder_spinbox.setSuffix(" pt")
        reminder_row.addWidget(self.reminder_spinbox)

        self.reminder_slider = QSlider(Qt.Orientation.Horizontal)
        self.reminder_slider.setRange(self.MIN_FONT_SIZE, self.MAX_FONT_SIZE)
        self.reminder_slider.setMaximumWidth(200)
        reminder_row.addWidget(self.reminder_slider)

        reminder_layout.addLayout(reminder_row)

        # 预览
        self.reminder_preview = QLabel("预览: 这是提醒内容的预览文本")
        reminder_layout.addWidget(self.reminder_preview)

        layout.addWidget(reminder_group)

        # 按钮
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self._save_and_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        # 连接信号
        self._connect_signals()

    def _connect_signals(self):
        """连接信号"""
        # 剪贴板面板 - spinbox 和 slider 同步
        self.clipboard_spinbox.valueChanged.connect(self._on_clipboard_spinbox_changed)
        self.clipboard_slider.valueChanged.connect(self._on_clipboard_slider_changed)

        # 提醒面板 - spinbox 和 slider 同步
        self.reminder_spinbox.valueChanged.connect(self._on_reminder_spinbox_changed)
        self.reminder_slider.valueChanged.connect(self._on_reminder_slider_changed)

    def _on_clipboard_spinbox_changed(self, value):
        """剪贴板 spinbox 值改变"""
        self.clipboard_slider.blockSignals(True)
        self.clipboard_slider.setValue(value)
        self.clipboard_slider.blockSignals(False)
        self._update_clipboard_preview(value)

    def _on_clipboard_slider_changed(self, value):
        """剪贴板 slider 值改变"""
        self.clipboard_spinbox.blockSignals(True)
        self.clipboard_spinbox.setValue(value)
        self.clipboard_spinbox.blockSignals(False)
        self._update_clipboard_preview(value)

    def _on_reminder_spinbox_changed(self, value):
        """提醒 spinbox 值改变"""
        self.reminder_slider.blockSignals(True)
        self.reminder_slider.setValue(value)
        self.reminder_slider.blockSignals(False)
        self._update_reminder_preview(value)

    def _on_reminder_slider_changed(self, value):
        """提醒 slider 值改变"""
        self.reminder_spinbox.blockSignals(True)
        self.reminder_spinbox.setValue(value)
        self.reminder_spinbox.blockSignals(False)
        self._update_reminder_preview(value)

    def _update_clipboard_preview(self, size):
        """更新剪贴板预览字体"""
        font = self.clipboard_preview.font()
        font.setPointSize(size)
        self.clipboard_preview.setFont(font)

    def _update_reminder_preview(self, size):
        """更新提醒预览字体"""
        font = self.reminder_preview.font()
        font.setPointSize(size)
        self.reminder_preview.setFont(font)

    def _load_settings(self):
        """加载当前设置"""
        cfg = self.config.data
        self.clipboard_spinbox.setValue(cfg.clipboard_font_size)
        self.reminder_spinbox.setValue(cfg.reminder_font_size)

    def _save_and_accept(self):
        """保存设置并关闭"""
        self.config.set('clipboard_font_size', self.clipboard_spinbox.value())
        self.config.set('reminder_font_size', self.reminder_spinbox.value())
        logger.info(f"字体设置已保存: 剪贴板={self.clipboard_spinbox.value()}pt, 提醒={self.reminder_spinbox.value()}pt")
        self.accept()

    def get_font_sizes(self):
        """获取设置的字体大小"""
        return {
            'clipboard_font_size': self.clipboard_spinbox.value(),
            'reminder_font_size': self.reminder_spinbox.value()
        }
