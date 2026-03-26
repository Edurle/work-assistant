"""剪贴板面板"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QListWidget, QListWidgetItem,
    QPushButton, QComboBox, QLabel, QMenu, QMessageBox, QInputDialog, QApplication
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QAction, QFont
from loguru import logger
from datetime import datetime

from src.clipboard.models import ClipboardItem, ContentType, Category


class ClipboardItemWidget(QListWidgetItem):
    """剪贴板项列表项"""

    def __init__(self, item: ClipboardItem):
        super().__init__()
        self.item_data = item
        self._update_display()

    def _update_display(self):
        """更新显示"""
        # 显示预览
        preview = self.item_data.preview or self.item_data.content[:100]
        self.setText(preview)

        # 设置提示
        self.setToolTip(f"类型: {self.item_data.content_type.value}\n时间: {self.item_data.created_at}")

        # 收藏标记
        if self.item_data.is_favorite:
            self.setText("⭐ " + self.text())


class ClipboardPanel(QWidget):
    """剪贴板面板"""

    item_copied = Signal(object)  # ClipboardItem

    def __init__(self, clipboard_manager, parent=None):
        super().__init__(parent)
        self.manager = clipboard_manager
        self._items: list[ClipboardItem] = []
        self._current_category = None
        self._init_ui()
        self._load_items()

    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        # 顶部工具栏
        toolbar = QHBoxLayout()

        # 搜索框
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索剪贴板内容...")
        self.search_input.textChanged.connect(self._on_search)
        toolbar.addWidget(self.search_input, 1)

        # 分类筛选
        self.category_combo = QComboBox()
        self.category_combo.addItem("全部分类", None)
        for cat in self.manager.get_categories():
            self.category_combo.addItem(cat.name, cat.id)
        self.category_combo.currentIndexChanged.connect(self._on_category_changed)
        toolbar.addWidget(self.category_combo)

        # 刷新按钮
        refresh_btn = QPushButton("刷新")
        refresh_btn.clicked.connect(self._load_items)
        toolbar.addWidget(refresh_btn)

        # 管理分类按钮
        manage_cat_btn = QPushButton("管理分类")
        manage_cat_btn.clicked.connect(self._manage_categories)
        toolbar.addWidget(manage_cat_btn)

        layout.addLayout(toolbar)

        # 列表
        self.list_widget = QListWidget()
        self.list_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self._show_context_menu)
        self.list_widget.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.list_widget.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self.list_widget)

        # 底部状态栏
        status_layout = QHBoxLayout()
        self.status_label = QLabel("共 0 条记录")
        status_layout.addWidget(self.status_label)

        # 清空按钮
        clear_btn = QPushButton("清空历史")
        clear_btn.clicked.connect(self._clear_history)
        status_layout.addWidget(clear_btn)

        layout.addLayout(status_layout)

    def _load_items(self):
        """加载剪贴板项"""
        self.list_widget.clear()
        self._items = self.manager.get_items(category_id=self._current_category, limit=200)

        for item in self._items:
            list_item = ClipboardItemWidget(item)
            self.list_widget.addItem(list_item)

        self.status_label.setText(f"共 {len(self._items)} 条记录")
        logger.debug(f"加载了 {len(self._items)} 条剪贴板记录")

    def add_item(self, item: ClipboardItem):
        """添加新的剪贴板项（从监控器接收）"""
        # 检查是否需要刷新
        if self._current_category is None or item.category_id == self._current_category:
            list_item = ClipboardItemWidget(item)
            self.list_widget.insertItem(0, list_item)
            self._items.insert(0, item)
            self.status_label.setText(f"共 {len(self._items)} 条记录")

    def _on_search(self, text: str):
        """搜索"""
        if not text:
            self._load_items()
            return

        self.list_widget.clear()
        results = self.manager.search(text)

        for item in results:
            list_item = ClipboardItemWidget(item)
            self.list_widget.addItem(list_item)

        self.status_label.setText(f"搜索结果: {len(results)} 条")

    def _on_category_changed(self, index: int):
        """分类改变"""
        self._current_category = self.category_combo.currentData()
        self._load_items()

    def _on_item_double_clicked(self, list_item: QListWidgetItem):
        """双击项 - 复制到剪贴板"""
        if isinstance(list_item, ClipboardItemWidget):
            item = list_item.item_data
            self.manager.copy_to_clipboard(item)
            self.item_copied.emit(item)

            # 显示提示
            self.status_label.setText(f"已复制: {item.preview[:30]}")

    def _on_item_clicked(self, list_item: QListWidgetItem):
        """单击项"""
        pass

    def _show_context_menu(self, pos):
        """显示右键菜单"""
        item = self.list_widget.itemAt(pos)
        if not item:
            return

        if not isinstance(item, ClipboardItemWidget):
            return

        clipboard_item = item.item_data

        menu = QMenu(self)

        # 复制
        copy_action = QAction("复制到剪贴板", self)
        copy_action.triggered.connect(lambda: self._copy_item(clipboard_item))
        menu.addAction(copy_action)

        # 收藏/取消收藏
        if clipboard_item.is_favorite:
            fav_action = QAction("取消收藏", self)
        else:
            fav_action = QAction("收藏", self)
        fav_action.triggered.connect(lambda: self._toggle_favorite(clipboard_item, item))
        menu.addAction(fav_action)

        menu.addSeparator()

        # 移动到分类
        cat_menu = menu.addMenu("移动到分类")
        for cat in self.manager.get_categories():
            cat_action = QAction(cat.name, self)
            cat_action.triggered.connect(lambda checked, c=cat, ci=clipboard_item: self._move_to_category(ci, c.id))
            cat_menu.addAction(cat_action)

        menu.addSeparator()

        # 删除
        delete_action = QAction("删除", self)
        delete_action.triggered.connect(lambda: self._delete_item(clipboard_item, item))
        menu.addAction(delete_action)

        menu.exec(self.list_widget.mapToGlobal(pos))

    def _copy_item(self, item: ClipboardItem):
        """复制项到剪贴板"""
        self.manager.copy_to_clipboard(item)
        self.status_label.setText(f"已复制: {item.preview[:30]}")

    def _toggle_favorite(self, item: ClipboardItem, list_item: ClipboardItemWidget):
        """切换收藏状态"""
        self.manager.toggle_favorite(item.id)
        item.is_favorite = not item.is_favorite
        list_item._update_display()

    def _move_to_category(self, item: ClipboardItem, category_id: int):
        """移动到分类"""
        self.manager.update_category(item.id, category_id)
        self._load_items()

    def _delete_item(self, item: ClipboardItem, list_item: ClipboardItemWidget):
        """删除项"""
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除这条记录吗？\n{item.preview[:50]}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.manager.delete_item(item.id)
            self.list_widget.takeItem(self.list_widget.row(list_item))
            self._items.remove(item)
            self.status_label.setText(f"共 {len(self._items)} 条记录")

    def _clear_history(self):
        """清空历史"""
        reply = QMessageBox.question(
            self, "确认清空",
            "确定要清空所有剪贴板历史吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            for item in self._items:
                self.manager.delete_item(item.id)
            self._load_items()

    def set_font_size(self, size: int):
        """设置字体大小"""
        font = QFont()
        font.setPointSize(size)

        # 应用到各个控件
        self.list_widget.setFont(font)
        self.search_input.setFont(font)
        self.category_combo.setFont(font)
        self.status_label.setFont(font)

        logger.debug(f"剪贴板面板字体大小设置为: {size}pt")

    def _manage_categories(self):
        """打开分类管理对话框"""
        from src.ui.category_dialog import CategoryManagerDialog
        dialog = CategoryManagerDialog(self.manager, self)
        dialog.exec()
        self._refresh_category_combo()

    def _refresh_category_combo(self):
        """刷新分类下拉框"""
        current_data = self.category_combo.currentData()
        self.category_combo.clear()
        self.category_combo.addItem("全部分类", None)
        for cat in self.manager.get_categories():
            self.category_combo.addItem(cat.name, cat.id)
        # 尝试恢复之前选中的分类
        for i in range(self.category_combo.count()):
            if self.category_combo.itemData(i) == current_data:
                self.category_combo.setCurrentIndex(i)
                break
