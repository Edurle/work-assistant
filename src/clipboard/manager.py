"""剪贴板管理模块"""

from typing import List, Optional
from datetime import datetime
from loguru import logger

from .models import ClipboardItem, Category, ContentType


class ClipboardManager:
    """剪贴板管理器"""

    # 预定义分类关键词
    AUTO_CATEGORIES = {
        '代码': ['def ', 'class ', 'import ', 'function', 'const ', 'let ', 'var ', 'public ', 'private ', 'return '],
        '链接': ['http://', 'https://', 'www.', '.com', '.org', '.net', '.cn/'],
        '图片': ['[图片]', '.png', '.jpg', '.jpeg', '.gif', '.bmp'],
    }

    def __init__(self, db):
        self.db = db
        self._categories: List[Category] = []
        self._load_categories()

    def _load_categories(self):
        """加载分类"""
        rows = self.db.fetchall("SELECT * FROM categories ORDER BY sort_order")
        self._categories = [Category.from_db_row(row) for row in rows]
        logger.debug(f"加载了 {len(self._categories)} 个分类")

    def get_categories(self) -> List[Category]:
        """获取所有分类"""
        return self._categories

    def auto_detect_category(self, content: str, content_type: ContentType) -> Optional[int]:
        """自动检测内容分类"""
        if content_type == ContentType.IMAGE:
            # 图片类型
            cat = next((c for c in self._categories if c.name == '图片'), None)
            return cat.id if cat else None

        content_lower = content.lower()

        for cat_name, keywords in self.AUTO_CATEGORIES.items():
            for keyword in keywords:
                if keyword.lower() in content_lower:
                    cat = next((c for c in self._categories if c.name == cat_name), None)
                    if cat:
                        return cat.id

        # 返回默认分类
        default_cat = next((c for c in self._categories if c.name == '默认'), None)
        return default_cat.id if default_cat else None

    def save_item(self, item: ClipboardItem) -> Optional[int]:
        """保存剪贴板项"""
        try:
            # 检查是否已存在（通过hash去重）
            existing = self.db.fetchone(
                "SELECT id, copy_count FROM clipboard_items WHERE hash = ?",
                (item.hash,)
            )

            if existing:
                # 已存在，增加复制次数
                self.db.update(
                    'clipboard_items',
                    {'copy_count': existing['copy_count'] + 1, 'updated_at': datetime.now().isoformat()},
                    'id = ?',
                    (existing['id'],)
                )
                logger.debug(f"剪贴板项已存在，更新复制次数: {existing['id']}")
                return existing['id']

            # 自动检测分类
            if item.category_id is None:
                item.category_id = self.auto_detect_category(item.content, item.content_type)

            # 插入新记录
            item_id = self.db.insert('clipboard_items', {
                'category_id': item.category_id,
                'content': item.content,
                'content_type': item.content_type.value,
                'preview': item.preview,
                'hash': item.hash,
                'is_favorite': 0,
                'is_deleted': 0,
                'copy_count': 1,
            })

            logger.info(f"保存剪贴板项: ID={item_id}, 类型={item.content_type.value}")
            return item_id

        except Exception as e:
            logger.error(f"保存剪贴板项失败: {e}")
            return None

    def get_items(self, category_id: Optional[int] = None, limit: int = 100, offset: int = 0) -> List[ClipboardItem]:
        """获取剪贴板项列表"""
        if category_id:
            rows = self.db.fetchall(
                "SELECT * FROM clipboard_items WHERE category_id = ? AND is_deleted = 0 ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (category_id, limit, offset)
            )
        else:
            rows = self.db.fetchall(
                "SELECT * FROM clipboard_items WHERE is_deleted = 0 ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (limit, offset)
            )

        return [ClipboardItem.from_db_row(row) for row in rows]

    def search(self, query: str, limit: int = 50) -> List[ClipboardItem]:
        """搜索剪贴板项"""
        if not query:
            return []

        search_pattern = f"%{query}%"
        rows = self.db.fetchall(
            """SELECT * FROM clipboard_items
               WHERE is_deleted = 0
               AND (content LIKE ? OR preview LIKE ?)
               ORDER BY created_at DESC LIMIT ?""",
            (search_pattern, search_pattern, limit)
        )

        return [ClipboardItem.from_db_row(row) for row in rows]

    def get_item(self, item_id: int) -> Optional[ClipboardItem]:
        """获取单个剪贴板项"""
        row = self.db.fetchone(
            "SELECT * FROM clipboard_items WHERE id = ? AND is_deleted = 0",
            (item_id,)
        )
        return ClipboardItem.from_db_row(row) if row else None

    def update_category(self, item_id: int, category_id: int) -> bool:
        """更新剪贴板项的分类"""
        try:
            self.db.update(
                'clipboard_items',
                {'category_id': category_id, 'updated_at': datetime.now().isoformat()},
                'id = ?',
                (item_id,)
            )
            logger.debug(f"更新剪贴板项分类: ID={item_id}, 分类ID={category_id}")
            return True
        except Exception as e:
            logger.error(f"更新分类失败: {e}")
            return False

    def toggle_favorite(self, item_id: int) -> bool:
        """切换收藏状态"""
        try:
            item = self.get_item(item_id)
            if item:
                self.db.update(
                    'clipboard_items',
                    {'is_favorite': not item.is_favorite, 'updated_at': datetime.now().isoformat()},
                    'id = ?',
                    (item_id,)
                )
                return True
            return False
        except Exception as e:
            logger.error(f"切换收藏状态失败: {e}")
            return False

    def delete_item(self, item_id: int, soft: bool = True) -> bool:
        """删除剪贴板项"""
        try:
            if soft:
                # 软删除
                self.db.update(
                    'clipboard_items',
                    {'is_deleted': 1, 'updated_at': datetime.now().isoformat()},
                    'id = ?',
                    (item_id,)
                )
            else:
                # 硬删除
                self.db.delete('clipboard_items', 'id = ?', (item_id,))

            logger.debug(f"删除剪贴板项: ID={item_id}, 软删除={soft}")
            return True
        except Exception as e:
            logger.error(f"删除失败: {e}")
            return False

    def get_favorites(self, limit: int = 50) -> List[ClipboardItem]:
        """获取收藏项"""
        rows = self.db.fetchall(
            "SELECT * FROM clipboard_items WHERE is_favorite = 1 AND is_deleted = 0 ORDER BY updated_at DESC LIMIT ?",
            (limit,)
        )
        return [ClipboardItem.from_db_row(row) for row in rows]

    def clear_old_items(self, days: int = 30) -> int:
        """清理旧记录"""
        try:
            count = self.db.delete(
                'clipboard_items',
                "is_deleted = 1 AND datetime(updated_at) < datetime('now', ?)",
                (f'-{days} days',)
            )
            logger.info(f"清理了 {count} 条旧记录")
            return count
        except Exception as e:
            logger.error(f"清理旧记录失败: {e}")
            return 0

    def copy_to_clipboard(self, item: ClipboardItem):
        """将内容复制到剪贴板"""
        from PySide6.QtWidgets import QApplication
        from PySide6.QtGui import QImage
        from PySide6.QtCore import QMimeData
        import base64

        clipboard = QApplication.clipboard()
        if not clipboard:
            return

        if item.content_type == ContentType.IMAGE:
            # 图片类型
            image_data = base64.b64decode(item.content)
            image = QImage()
            image.loadFromData(image_data)
            clipboard.setImage(image)
        else:
            # 文本类型
            clipboard.setText(item.content)

        logger.debug(f"已复制到剪贴板: ID={item.id}")

    # ========== 分类管理方法 ==========

    def create_category(self, name: str, color: str = "#3498db", icon: str = "folder") -> Optional[Category]:
        """创建分类"""
        try:
            # 获取最大排序值
            max_order = self.db.fetchone("SELECT MAX(sort_order) as max_order FROM categories")
            sort_order = (max_order['max_order'] or 0) + 1

            category_id = self.db.insert('categories', {
                'name': name,
                'color': color,
                'icon': icon,
                'sort_order': sort_order,
            })

            # 重新加载分类
            self._load_categories()

            # 返回新创建的分类
            return next((c for c in self._categories if c.id == category_id), None)
        except Exception as e:
            logger.error(f"创建分类失败: {e}")
            return None

    def update_category_info(self, category_id: int, name: str = None, color: str = None, icon: str = None) -> bool:
        """更新分类信息"""
        try:
            data = {'updated_at': datetime.now().isoformat()}
            if name is not None:
                data['name'] = name
            if color is not None:
                data['color'] = color
            if icon is not None:
                data['icon'] = icon

            self.db.update('categories', data, 'id = ?', (category_id,))
            self._load_categories()
            logger.debug(f"更新分类: ID={category_id}")
            return True
        except Exception as e:
            logger.error(f"更新分类失败: {e}")
            return False

    def delete_category(self, category_id: int) -> bool:
        """删除分类（将关联项移到默认分类）"""
        try:
            # 不允许删除默认分类
            if category_id == 1:
                logger.warning("不能删除默认分类")
                return False

            # 将该分类下的所有剪贴板项移到默认分类
            self.db.update(
                'clipboard_items',
                {'category_id': 1, 'updated_at': datetime.now().isoformat()},
                'category_id = ?',
                (category_id,)
            )

            # 删除分类
            self.db.delete('categories', 'id = ?', (category_id,))
            self._load_categories()
            logger.info(f"删除分类: ID={category_id}")
            return True
        except Exception as e:
            logger.error(f"删除分类失败: {e}")
            return False

    def reorder_category(self, category_id: int, new_order: int) -> bool:
        """调整分类排序"""
        try:
            self.db.update(
                'categories',
                {'sort_order': new_order, 'updated_at': datetime.now().isoformat()},
                'id = ?',
                (category_id,)
            )
            self._load_categories()
            return True
        except Exception as e:
            logger.error(f"调整分类排序失败: {e}")
            return False

    def refresh_categories(self):
        """刷新分类列表"""
        self._load_categories()
