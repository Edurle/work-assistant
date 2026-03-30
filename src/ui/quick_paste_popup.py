"""快速粘贴弹窗模块"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QListWidget, QListWidgetItem,
    QLabel, QFrame, QLineEdit, QScrollArea, QDialog
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QKeySequence, QShortcut, QGuiApplication, QImage, QPixmap
from pynput.keyboard import Controller, Key
from loguru import logger
import base64

from src.clipboard.models import ClipboardItem, Category, ContentType


class ContentPreviewDialog(QDialog):
    """内容预览对话框"""

    def __init__(self, item: ClipboardItem, parent=None):
        super().__init__(parent)
        self.item = item
        self._setup_window()
        self._init_ui()

    def _setup_window(self):
        """设置窗口属性"""
        self.setWindowTitle("内容预览")
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Dialog
        )
        self.setMinimumSize(500, 400)
        self.resize(600, 500)

    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)

        if self.item.content_type == ContentType.IMAGE:
            # 图片类型
            self._show_image(layout)
        else:
            # 文本类型
            self._show_text(layout)

        # 关闭提示
        hint_label = QLabel("按 Esc 或点击关闭")
        hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint_label.setStyleSheet("color: #888; font-size: 11px; padding: 10px;")
        layout.addWidget(hint_label)

    def _show_image(self, layout: QVBoxLayout):
        """显示图片"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: #f5f5f5; }")

        image_label = QLabel()
        image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        image_label.setStyleSheet("background-color: #f5f5f5;")

        try:
            image_data = base64.b64decode(self.item.content)
            image = QImage()
            if image.loadFromData(image_data):
                # 缩放图片以适应窗口
                pixmap = QPixmap.fromImage(image)
                if pixmap.width() > 800 or pixmap.height() > 600:
                    pixmap = pixmap.scaled(
                        800, 600,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )
                image_label.setPixmap(pixmap)
            else:
                image_label.setText("无法加载图片")
                image_label.setStyleSheet("color: #e74c3c; font-size: 14px;")
        except Exception as e:
            logger.error(f"显示图片失败: {e}")
            image_label.setText(f"图片加载失败: {e}")
            image_label.setStyleSheet("color: #e74c3c; font-size: 14px;")

        scroll.setWidget(image_label)
        layout.addWidget(scroll, 1)

    def _show_text(self, layout: QVBoxLayout):
        """显示文本"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: 1px solid #ddd;
                border-radius: 5px;
                background-color: white;
            }
        """)

        text_label = QLabel()
        text_label.setWordWrap(True)
        text_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        text_label.setStyleSheet("""
            QLabel {
                padding: 15px;
                font-size: 13px;
                line-height: 1.5;
                background-color: white;
            }
        """)
        text_label.setText(self.item.content or "(空内容)")

        scroll.setWidget(text_label)
        layout.addWidget(scroll, 1)

    def keyPressEvent(self, event):
        """按键事件 - Esc关闭"""
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)


class QuickPastePopup(QWidget):
    """快速粘贴弹窗"""

    def __init__(self, clipboard_manager, parent=None):
        super().__init__(parent)
        self.manager = clipboard_manager
        self._items: list[ClipboardItem] = []
        self._categories: list[Category] = []
        self._current_category_index: int = 0
        self._search_mode: bool = False

        self._setup_window()
        self._init_ui()
        self._setup_shortcuts()

    def _setup_window(self):
        """设置窗口属性"""
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(400, 500)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def _init_ui(self):
        """初始化UI"""
        self.container = QFrame()
        self.container.setObjectName("popupContainer")
        self.container.setStyleSheet("""
            #popupContainer {
                background-color: rgba(255, 255, 255, 245);
                border-radius: 10px;
                border: 1px solid #ddd;
            }
            QListWidget {
                border: none;
                background-color: transparent;
                font-size: 13px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #eee;
            }
            QListWidget::item:selected {
                background-color: #3498db;
                color: white;
                outline: none;
            }
            QListWidget::item:hover:!selected {
                background-color: #ecf0f1;
            }
            QLabel#headerLabel {
                font-size: 14px;
                font-weight: bold;
                padding: 10px;
            }
            QLabel#footerLabel {
                font-size: 11px;
                color: #888;
                padding: 5px;
            }
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.addWidget(self.container)

        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        # 标题栏
        self.header_label = QLabel("剪贴板历史 (Alt+V)")
        self.header_label.setObjectName("headerLabel")
        self.header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.addWidget(self.header_label)

        # 搜索框（初始隐藏）
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入搜索内容...")
        self.search_input.setObjectName("searchInput")
        self.search_input.setStyleSheet("""
            QLineEdit#searchInput {
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 13px;
            }
        """)
        self.search_input.textChanged.connect(self._on_search)
        self.search_input.hide()
        container_layout.addWidget(self.search_input)

        # 列表
        self.list_widget = QListWidget()
        self.list_widget.setSelectionBehavior(QListWidget.SelectionBehavior.SelectRows)
        self.list_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.list_widget.itemDoubleClicked.connect(self._paste_selected)
        container_layout.addWidget(self.list_widget, 1)

        # 底部提示
        self.footer_label = QLabel("Q 搜索 | A/D 分类 | W/S 选择 | F 粘贴 | R 预览 | Esc 关闭")
        self.footer_label.setObjectName("footerLabel")
        self.footer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.addWidget(self.footer_label)

    def _setup_shortcuts(self):
        """设置快捷键"""
        # Esc 关闭或退出搜索
        esc_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Escape), self)
        esc_shortcut.activated.connect(self._on_escape)

        # Enter 粘贴
        enter_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Return), self)
        enter_shortcut.activated.connect(self._paste_selected)

        # Ctrl+V 粘贴
        ctrl_v_shortcut = QShortcut(QKeySequence("Ctrl+V"), self)
        ctrl_v_shortcut.activated.connect(self._paste_selected)

        # 上下箭头导航
        up_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Up), self)
        up_shortcut.activated.connect(self._select_previous)

        down_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Down), self)
        down_shortcut.activated.connect(self._select_next)

        # Q 进入搜索
        q_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Q), self)
        q_shortcut.activated.connect(self._enter_search_mode)

        # A/D 切换分类
        a_shortcut = QShortcut(QKeySequence(Qt.Key.Key_A), self)
        a_shortcut.activated.connect(self._prev_category)

        d_shortcut = QShortcut(QKeySequence(Qt.Key.Key_D), self)
        d_shortcut.activated.connect(self._next_category)

        # W/S 选择项目
        w_shortcut = QShortcut(QKeySequence(Qt.Key.Key_W), self)
        w_shortcut.activated.connect(self._select_previous)

        s_shortcut = QShortcut(QKeySequence(Qt.Key.Key_S), self)
        s_shortcut.activated.connect(self._select_next)

        # F 粘贴
        f_shortcut = QShortcut(QKeySequence(Qt.Key.Key_F), self)
        f_shortcut.activated.connect(self._paste_selected)

        # R 预览完整内容
        r_shortcut = QShortcut(QKeySequence(Qt.Key.Key_R), self)
        r_shortcut.activated.connect(self._show_preview)

    def show_popup(self):
        """显示弹窗"""
        # 加载分类数据
        self._categories = self.manager.get_categories()
        self._current_category_index = 0

        self._load_items()
        self._update_header()
        self._position_window()
        self.show()
        self.raise_()
        self.activateWindow()
        self.list_widget.setFocus()
        if self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)

    def hide_popup(self):
        """隐藏弹窗"""
        self.hide()

    def _position_window(self):
        """定位窗口 - 屏幕中央偏上"""
        screen = QGuiApplication.primaryScreen().availableGeometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 3
        self.move(x, y)

    def _load_items(self):
        """加载剪贴板项"""
        self.list_widget.clear()

        # 获取当前分类ID
        if self._categories and 0 <= self._current_category_index < len(self._categories):
            category_id = self._categories[self._current_category_index].id
        else:
            category_id = None

        # 加载该分类的项
        self._items = self.manager.get_items(
            category_id=category_id,
            limit=50
        )

        for item in self._items:
            list_item = QListWidgetItem()
            preview = item.preview or (item.content[:80] if item.content else "")
            if item.is_favorite:
                preview = "⭐ " + preview
            list_item.setText(preview)
            list_item.setData(Qt.ItemDataRole.UserRole, item.id)
            self.list_widget.addItem(list_item)

    def _paste_selected(self):
        """粘贴选中项"""
        current = self.list_widget.currentItem()
        if not current:
            return

        item_id = current.data(Qt.ItemDataRole.UserRole)
        clipboard_item = next((i for i in self._items if i.id == item_id), None)

        if clipboard_item:
            # 复制到剪贴板
            self.manager.copy_to_clipboard(clipboard_item)

            # 延迟执行粘贴
            self.hide_popup()
            QTimer.singleShot(100, self._do_paste)

    def _show_preview(self):
        """显示选中项的完整内容预览"""
        current = self.list_widget.currentItem()
        if not current:
            return

        item_id = current.data(Qt.ItemDataRole.UserRole)
        clipboard_item = next((i for i in self._items if i.id == item_id), None)

        if clipboard_item:
            # 获取主窗口位置，在右侧显示预览
            main_rect = self.geometry()
            preview_dialog = ContentPreviewDialog(clipboard_item, self)
            preview_dialog.move(main_rect.right() + 10, main_rect.top())
            preview_dialog.exec()

    def _do_paste(self):
        """执行粘贴操作"""
        try:
            keyboard = Controller()
            keyboard.press(Key.ctrl)
            keyboard.press('v')
            keyboard.release('v')
            keyboard.release(Key.ctrl)
            logger.debug("已模拟 Ctrl+V 粘贴")
        except Exception as e:
            logger.error(f"模拟粘贴失败: {e}")

    def _select_previous(self):
        """选择上一项"""
        row = self.list_widget.currentRow()
        if row > 0:
            self.list_widget.setCurrentRow(row - 1)

    def _select_next(self):
        """选择下一项"""
        row = self.list_widget.currentRow()
        if row < self.list_widget.count() - 1:
            self.list_widget.setCurrentRow(row + 1)

    def _update_header(self):
        """更新标题栏显示"""
        if self._categories and 0 <= self._current_category_index < len(self._categories):
            cat_name = self._categories[self._current_category_index].name
            cat_count = len(self._categories)
            self.header_label.setText(f"剪贴板历史 - {cat_name} ({self._current_category_index + 1}/{cat_count})")
        else:
            self.header_label.setText("剪贴板历史 (Alt+V)")

    def _prev_category(self):
        """切换到上一个分类"""
        if not self._categories:
            return

        self._current_category_index -= 1
        if self._current_category_index < 0:
            self._current_category_index = len(self._categories) - 1

        self._on_category_changed()

    def _next_category(self):
        """切换到下一个分类"""
        if not self._categories:
            return

        self._current_category_index += 1
        if self._current_category_index >= len(self._categories):
            self._current_category_index = 0

        self._on_category_changed()

    def _on_category_changed(self):
        """分类变化处理"""
        self._load_items()
        self._update_header()
        if self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)

    def _on_escape(self):
        """处理Esc键"""
        if self._search_mode:
            self._exit_search_mode()
        else:
            self.hide_popup()

    def _enter_search_mode(self):
        """进入搜索模式"""
        self._search_mode = True
        self.search_input.show()
        self.search_input.clear()
        self.search_input.setFocus()
        self.footer_label.setText("Enter 粘贴 | Esc 退出搜索")

    def _exit_search_mode(self):
        """退出搜索模式"""
        self._search_mode = False
        self.search_input.hide()
        self.search_input.clear()
        self._load_items()
        self.list_widget.setFocus()
        if self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)
        self.footer_label.setText("Q 搜索 | A/D 分类 | W/S 选择 | F 粘贴 | Esc 关闭")

    def _on_search(self, text: str):
        """搜索过滤"""
        if not self._search_mode:
            return

        self.list_widget.clear()

        if not text:
            # 空搜索，显示所有项
            self._update_header()
            for item in self._items:
                self._add_list_item(item)
            return

        # 过滤匹配的项
        query = text.lower()
        for item in self._items:
            content = (item.content or "").lower()
            preview = (item.preview or "").lower()
            if query in content or query in preview:
                self._add_list_item(item)

        # 更新标题显示搜索结果数
        count = self.list_widget.count()
        self.header_label.setText(f"搜索结果: {count} 条")

        if count > 0:
            self.list_widget.setCurrentRow(0)

    def _add_list_item(self, item: ClipboardItem):
        """添加列表项"""
        list_item = QListWidgetItem()
        preview = item.preview or (item.content[:80] if item.content else "")
        if item.is_favorite:
            preview = "⭐ " + preview
        list_item.setText(preview)
        list_item.setData(Qt.ItemDataRole.UserRole, item.id)
        self.list_widget.addItem(list_item)

    def focusOutEvent(self, event):
        """失去焦点时关闭"""
        QTimer.singleShot(150, self._check_focus)

    def _check_focus(self):
        """检查焦点"""
        if not self.isVisible():
            return
        if self._search_mode:
            # 搜索模式下检查搜索框焦点
            if not self.hasFocus() and not self.list_widget.hasFocus() and not self.search_input.hasFocus():
                self.hide_popup()
        else:
            if not self.hasFocus() and not self.list_widget.hasFocus():
                self.hide_popup()
