"""分类管理对话框模块"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QLabel, QLineEdit, QColorDialog, QMessageBox, QWidget
)
from PySide6.QtGui import QColor, QFont
from PySide6.QtCore import Qt
from loguru import logger


class CategoryItemWidget(QWidget):
    """分类列表项组件"""

    def __init__(self, category, parent=None):
        super().__init__(parent)
        self.category = category
        self._init_ui()

    def _init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)

        # 颜色标记
        self.color_label = QLabel("●")
        self.color_label.setStyleSheet(f"color: {self.category.color}; font-size: 16px;")
        layout.addWidget(self.color_label)

        # 名称
        self.name_label = QLabel(self.category.name)
        layout.addWidget(self.name_label, 1)

    def update_display(self, category):
        self.category = category
        self.color_label.setStyleSheet(f"color: {self.category.color}; font-size: 16px;")
        self.name_label.setText(self.category.name)


class EditCategoryDialog(QDialog):
    """编辑分类对话框"""

    def __init__(self, category=None, parent=None):
        super().__init__(parent)
        self.category = category
        self.selected_color = category.color if category else "#3498db"
        self._init_ui()

    def _init_ui(self):
        self.setWindowTitle("编辑分类" if self.category else "新建分类")
        self.setMinimumWidth(300)

        layout = QVBoxLayout(self)

        # 名称
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("名称:"))
        self.name_input = QLineEdit()
        if self.category:
            self.name_input.setText(self.category.name)
        name_layout.addWidget(self.name_input)
        layout.addLayout(name_layout)

        # 颜色
        color_layout = QHBoxLayout()
        color_layout.addWidget(QLabel("颜色:"))
        self.color_btn = QPushButton()
        self.color_btn.setFixedSize(60, 30)
        self._update_color_btn()
        self.color_btn.clicked.connect(self._choose_color)
        color_layout.addWidget(self.color_btn)
        color_layout.addStretch()
        layout.addLayout(color_layout)

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

    def _update_color_btn(self):
        self.color_btn.setStyleSheet(f"background-color: {self.selected_color}; border: 1px solid #ccc;")

    def _choose_color(self):
        color = QColorDialog.getColor(QColor(self.selected_color), self, "选择颜色")
        if color.isValid():
            self.selected_color = color.name()
            self._update_color_btn()

    def _save(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "提示", "请输入分类名称")
            return
        self.accept()

    def get_data(self):
        return {
            'name': self.name_input.text().strip(),
            'color': self.selected_color,
        }


class CategoryManagerDialog(QDialog):
    """分类管理对话框"""

    def __init__(self, clipboard_manager, parent=None):
        super().__init__(parent)
        self.manager = clipboard_manager
        self._init_ui()
        self._load_categories()

    def _init_ui(self):
        self.setWindowTitle("管理分类")
        self.setMinimumSize(400, 350)

        layout = QVBoxLayout(self)

        # 提示
        hint = QLabel("双击分类可编辑，拖动可调整顺序")
        hint.setStyleSheet("color: gray; font-size: 11px;")
        layout.addWidget(hint)

        # 分类列表
        self.list_widget = QListWidget()
        self.list_widget.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self.list_widget.model().rowsMoved.connect(self._on_rows_moved)
        self.list_widget.itemDoubleClicked.connect(self._edit_category)
        layout.addWidget(self.list_widget)

        # 操作按钮
        btn_layout = QHBoxLayout()

        self.add_btn = QPushButton("新建")
        self.add_btn.clicked.connect(self._add_category)
        btn_layout.addWidget(self.add_btn)

        self.edit_btn = QPushButton("编辑")
        self.edit_btn.clicked.connect(self._edit_selected)
        btn_layout.addWidget(self.edit_btn)

        self.delete_btn = QPushButton("删除")
        self.delete_btn.clicked.connect(self._delete_category)
        btn_layout.addWidget(self.delete_btn)

        btn_layout.addStretch()

        self.up_btn = QPushButton("↑")
        self.up_btn.setFixedWidth(40)
        self.up_btn.clicked.connect(self._move_up)
        btn_layout.addWidget(self.up_btn)

        self.down_btn = QPushButton("↓")
        self.down_btn.setFixedWidth(40)
        self.down_btn.clicked.connect(self._move_down)
        btn_layout.addWidget(self.down_btn)

        layout.addLayout(btn_layout)

        # 关闭按钮
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

    def _load_categories(self):
        self.list_widget.clear()
        categories = self.manager.get_categories()
        for cat in categories:
            item = QListWidgetItem()
            widget = CategoryItemWidget(cat)
            item.setSizeHint(widget.sizeHint())
            item.setData(Qt.ItemDataRole.UserRole, cat.id)
            self.list_widget.addItem(item)
            self.list_widget.setItemWidget(item, widget)

    def _add_category(self):
        dialog = EditCategoryDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            self.manager.create_category(data['name'], data['color'])
            self._load_categories()
            logger.info(f"创建分类: {data['name']}")

    def _edit_category(self, item):
        category_id = item.data(Qt.ItemDataRole.UserRole)
        categories = self.manager.get_categories()
        category = next((c for c in categories if c.id == category_id), None)
        if not category:
            return

        dialog = EditCategoryDialog(category=category, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            self.manager.update_category_info(category_id, data['name'], data['color'])
            self._load_categories()
            logger.info(f"更新分类: {data['name']}")

    def _edit_selected(self):
        item = self.list_widget.currentItem()
        if item:
            self._edit_category(item)

    def _delete_category(self):
        item = self.list_widget.currentItem()
        if not item:
            return

        category_id = item.data(Qt.ItemDataRole.UserRole)

        # 不允许删除默认分类
        if category_id == 1:
            QMessageBox.warning(self, "提示", "不能删除默认分类")
            return

        categories = self.manager.get_categories()
        category = next((c for c in categories if c.id == category_id), None)
        if not category:
            return

        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除分类「{category.name}」吗？\n该分类下的剪贴板项将移到「默认」分类。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.manager.delete_category(category_id)
            self._load_categories()
            logger.info(f"删除分类: {category.name}")

    def _move_up(self):
        current_row = self.list_widget.currentRow()
        if current_row > 0:
            self._swap_order(current_row, current_row - 1)

    def _move_down(self):
        current_row = self.list_widget.currentRow()
        if current_row < self.list_widget.count() - 1:
            self._swap_order(current_row, current_row + 1)

    def _swap_order(self, row1, row2):
        """交换两个分类的顺序"""
        item1 = self.list_widget.item(row1)
        item2 = self.list_widget.item(row2)
        if not item1 or not item2:
            return

        id1 = item1.data(Qt.ItemDataRole.UserRole)
        id2 = item2.data(Qt.ItemDataRole.UserRole)

        # 更新排序
        categories = self.manager.get_categories()
        for i, cat in enumerate(categories):
            new_order = i
            if cat.id == id1:
                new_order = row2
            elif cat.id == id2:
                new_order = row1
            if new_order != i:
                self.manager.reorder_category(cat.id, new_order)

        self._load_categories()
        self.list_widget.setCurrentRow(row2)

    def _on_rows_moved(self):
        """拖动完成后更新排序"""
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            category_id = item.data(Qt.ItemDataRole.UserRole)
            self.manager.reorder_category(category_id, i)
