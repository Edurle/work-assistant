"""提醒面板"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QListWidget, QListWidgetItem,
    QPushButton, QComboBox, QLabel, QMenu, QMessageBox, QDialog, QFormLayout,
    QDateTimeEdit, QSpinBox, QCheckBox, QTextEdit, QGroupBox, QRadioButton
)
from PySide6.QtCore import Qt, Signal, QDateTime
from PySide6.QtGui import QAction, QFont
from loguru import logger
from datetime import datetime, timedelta

from src.reminder.models import Reminder, ReminderType, IntervalUnit


class ReminderItemWidget(QListWidgetItem):
    """提醒项列表项"""

    def __init__(self, reminder: Reminder):
        super().__init__()
        self.reminder_data = reminder
        self._update_display()

    def _update_display(self):
        """更新显示"""
        r = self.reminder_data

        # 类型标记
        type_mark = "⏰" if r.reminder_type == ReminderType.POINT else "🔄"

        # 状态标记
        status = "" if r.is_enabled else " [已禁用]"

        # 显示文本
        self.setText(f"{type_mark} {r.title}{status}")

        # 设置提示
        next_str = r.next_trigger.strftime("%Y-%m-%d %H:%M:%S") if r.next_trigger else "未设置"
        self.setToolTip(f"下次触发: {next_str}\n类型: {r.reminder_type.value}")


class AddReminderDialog(QDialog):
    """添加提醒对话框"""

    def __init__(self, reminder: Reminder = None, parent=None):
        super().__init__(parent)
        self.reminder = reminder or Reminder()
        self._init_ui()
        if reminder:
            self._load_reminder()

    def _init_ui(self):
        """初始化UI"""
        self.setWindowTitle("添加提醒" if not self.reminder.id else "编辑提醒")
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)

        # 表单
        form = QFormLayout()

        # 标题
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("提醒标题")
        form.addRow("标题:", self.title_input)

        # 内容
        self.content_input = QTextEdit()
        self.content_input.setPlaceholderText("提醒内容（可选）")
        self.content_input.setMaximumHeight(80)
        form.addRow("内容:", self.content_input)

        # 类型选择
        type_group = QGroupBox("提醒类型")
        type_layout = QHBoxLayout(type_group)

        self.point_radio = QRadioButton("时间点")
        self.point_radio.setChecked(True)
        self.point_radio.toggled.connect(self._on_type_changed)
        type_layout.addWidget(self.point_radio)

        self.interval_radio = QRadioButton("间隔")
        self.interval_radio.toggled.connect(self._on_type_changed)
        type_layout.addWidget(self.interval_radio)

        form.addRow(type_group)

        # 时间点设置
        self.point_group = QGroupBox("时间点设置")
        point_layout = QFormLayout(self.point_group)

        self.datetime_edit = QDateTimeEdit()
        self.datetime_edit.setCalendarPopup(True)
        self.datetime_edit.setDateTime(QDateTime.currentDateTime().addSecs(3600))  # 默认1小时后
        point_layout.addRow("触发时间:", self.datetime_edit)

        form.addRow(self.point_group)

        # 间隔设置
        self.interval_group = QGroupBox("间隔设置")
        interval_layout = QFormLayout(self.interval_group)

        interval_row = QHBoxLayout()
        self.interval_value = QSpinBox()
        self.interval_value.setRange(1, 9999)
        self.interval_value.setValue(30)
        interval_row.addWidget(self.interval_value)

        self.interval_unit = QComboBox()
        self.interval_unit.addItems(["秒", "分钟", "小时", "天"])
        self.interval_unit.setCurrentIndex(1)  # 默认分钟
        interval_row.addWidget(self.interval_unit)
        interval_layout.addRow("间隔时间:", interval_row)

        self.recurring_check = QCheckBox("重复")
        self.recurring_check.setChecked(True)
        interval_layout.addRow(self.recurring_check)

        form.addRow(self.interval_group)
        self.interval_group.setVisible(False)

        # 其他设置
        self.sound_check = QCheckBox("启用声音")
        self.sound_check.setChecked(True)
        form.addRow(self.sound_check)

        layout.addLayout(form)

        # 按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        save_btn = QPushButton("保存")
        save_btn.clicked.connect(self._save)
        save_btn.setDefault(True)
        button_layout.addWidget(save_btn)

        layout.addLayout(button_layout)

    def _on_type_changed(self):
        """类型改变"""
        is_point = self.point_radio.isChecked()
        self.point_group.setVisible(is_point)
        self.interval_group.setVisible(not is_point)

    def _load_reminder(self):
        """加载提醒数据"""
        r = self.reminder
        self.title_input.setText(r.title)
        self.content_input.setPlainText(r.content or "")

        if r.reminder_type == ReminderType.POINT:
            self.point_radio.setChecked(True)
            if r.trigger_time:
                self.datetime_edit.setDateTime(QDateTime.fromString(
                    r.trigger_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "yyyy-MM-dd HH:mm:ss"
                ))
        else:
            self.interval_radio.setChecked(True)
            self.interval_value.setValue(r.interval_value)
            unit_map = {"seconds": 0, "minutes": 1, "hours": 2, "days": 3}
            self.interval_unit.setCurrentIndex(unit_map.get(r.interval_unit.value, 1))
            self.recurring_check.setChecked(r.is_recurring)

        self.sound_check.setChecked(r.sound_enabled)

    def _save(self):
        """保存"""
        title = self.title_input.text().strip()
        if not title:
            QMessageBox.warning(self, "提示", "请输入提醒标题")
            return

        self.reminder.title = title
        self.reminder.content = self.content_input.toPlainText()
        self.reminder.reminder_type = ReminderType.POINT if self.point_radio.isChecked() else ReminderType.INTERVAL

        if self.reminder.reminder_type == ReminderType.POINT:
            self.reminder.trigger_time = self.datetime_edit.dateTime().toPython()
        else:
            self.reminder.interval_value = self.interval_value.value()
            unit_map = {0: IntervalUnit.SECONDS, 1: IntervalUnit.MINUTES, 2: IntervalUnit.HOURS, 3: IntervalUnit.DAYS}
            self.reminder.interval_unit = unit_map[self.interval_unit.currentIndex()]
            self.reminder.is_recurring = self.recurring_check.isChecked()

        self.reminder.sound_enabled = self.sound_check.isChecked()

        self.accept()

    def get_reminder(self) -> Reminder:
        """获取提醒对象"""
        return self.reminder


class ReminderPanel(QWidget):
    """提醒面板"""

    reminder_updated = Signal()

    def __init__(self, scheduler, parent=None):
        super().__init__(parent)
        self.scheduler = scheduler
        self._reminders: list[Reminder] = []
        self._init_ui()
        self._load_reminders()

    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        # 顶部工具栏
        toolbar = QHBoxLayout()

        # 添加提醒按钮
        add_btn = QPushButton("新建提醒")
        add_btn.clicked.connect(self._add_reminder)
        toolbar.addWidget(add_btn)

        # 筛选
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["全部", "已启用", "已禁用"])
        self.filter_combo.currentIndexChanged.connect(self._load_reminders)
        toolbar.addWidget(self.filter_combo)

        toolbar.addStretch()

        # 刷新
        refresh_btn = QPushButton("刷新")
        refresh_btn.clicked.connect(self._load_reminders)
        toolbar.addWidget(refresh_btn)

        layout.addLayout(toolbar)

        # 列表
        self.list_widget = QListWidget()
        self.list_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self._show_context_menu)
        self.list_widget.itemDoubleClicked.connect(self._edit_reminder)
        layout.addWidget(self.list_widget)

        # 底部状态
        status_layout = QHBoxLayout()
        self.status_label = QLabel("共 0 条提醒")
        status_layout.addWidget(self.status_label)
        layout.addLayout(status_layout)

    def _load_reminders(self):
        """加载提醒列表"""
        self.list_widget.clear()

        filter_type = self.filter_combo.currentIndex()
        all_reminders = self.scheduler.get_all_reminders()

        if filter_type == 1:  # 已启用
            self._reminders = [r for r in all_reminders if r.is_enabled]
        elif filter_type == 2:  # 已禁用
            self._reminders = [r for r in all_reminders if not r.is_enabled]
        else:
            self._reminders = all_reminders

        for reminder in self._reminders:
            item = ReminderItemWidget(reminder)
            self.list_widget.addItem(item)

        self.status_label.setText(f"共 {len(self._reminders)} 条提醒")

    def _add_reminder(self):
        """添加提醒"""
        dialog = AddReminderDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            reminder = dialog.get_reminder()
            self.scheduler.add_reminder(reminder)
            self._load_reminders()
            self.status_label.setText("提醒已添加")

    def _edit_reminder(self, list_item: QListWidgetItem):
        """编辑提醒"""
        if not isinstance(list_item, ReminderItemWidget):
            return

        reminder = list_item.reminder_data
        dialog = AddReminderDialog(reminder=reminder, parent=self)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            updated = dialog.get_reminder()
            self.scheduler.update_reminder(updated)
            self._load_reminders()
            self.status_label.setText("提醒已更新")

    def _show_context_menu(self, pos):
        """显示右键菜单"""
        item = self.list_widget.itemAt(pos)
        if not item or not isinstance(item, ReminderItemWidget):
            return

        reminder = item.reminder_data

        menu = QMenu(self)

        # 编辑
        edit_action = QAction("编辑", self)
        edit_action.triggered.connect(lambda: self._edit_reminder(item))
        menu.addAction(edit_action)

        # 启用/禁用
        if reminder.is_enabled:
            toggle_action = QAction("禁用", self)
        else:
            toggle_action = QAction("启用", self)
        toggle_action.triggered.connect(lambda: self._toggle_reminder(reminder))
        menu.addAction(toggle_action)

        menu.addSeparator()

        # 删除
        delete_action = QAction("删除", self)
        delete_action.triggered.connect(lambda: self._delete_reminder(reminder, item))
        menu.addAction(delete_action)

        menu.exec(self.list_widget.mapToGlobal(pos))

    def _toggle_reminder(self, reminder: Reminder):
        """切换提醒状态"""
        self.scheduler.toggle_enabled(reminder.id)
        self._load_reminders()

    def _delete_reminder(self, reminder: Reminder, list_item: ReminderItemWidget):
        """删除提醒"""
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除提醒「{reminder.title}」吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.scheduler.remove_reminder(reminder.id)
            self.list_widget.takeItem(self.list_widget.row(list_item))
            self._reminders.remove(reminder)
            self.status_label.setText(f"共 {len(self._reminders)} 条提醒")

    def set_font_size(self, size: int):
        """设置字体大小"""
        font = QFont()
        font.setPointSize(size)

        # 应用到各个控件
        self.list_widget.setFont(font)
        self.filter_combo.setFont(font)
        self.status_label.setFont(font)

        logger.debug(f"提醒面板字体大小设置为: {size}pt")
