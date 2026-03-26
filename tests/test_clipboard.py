"""剪贴板模块测试"""

import pytest
from pathlib import Path
import tempfile
import os

# 添加src到路径
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from clipboard.models import ClipboardItem, ContentType, Category
from core.database import Database


class TestClipboardItem:
    """剪贴板项测试"""

    def test_create_text_item(self):
        """测试创建文本项"""
        item = ClipboardItem(
            content="Hello, World!",
            content_type=ContentType.TEXT,
            preview="Hello, World!"
        )
        assert item.content == "Hello, World!"
        assert item.content_type == ContentType.TEXT

    def test_generate_hash(self):
        """测试哈希生成"""
        hash1 = ClipboardItem.generate_hash("test", ContentType.TEXT)
        hash2 = ClipboardItem.generate_hash("test", ContentType.TEXT)
        hash3 = ClipboardItem.generate_hash("test", ContentType.HTML)

        assert hash1 == hash2  # 相同内容和类型生成相同哈希
        assert hash1 != hash3  # 不同类型生成不同哈希
        assert len(hash1) == 16  # 哈希长度为16

    def test_to_dict(self):
        """测试转换为字典"""
        item = ClipboardItem(
            id=1,
            content="test",
            content_type=ContentType.TEXT,
            preview="test"
        )
        d = item.to_dict()
        assert d['id'] == 1
        assert d['content'] == "test"
        assert d['content_type'] == "text"


class TestDatabase:
    """数据库测试"""

    @pytest.fixture
    def temp_db(self):
        """创建临时数据库"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name

        # 重置单例
        Database._instance = None
        db = Database(db_path)
        yield db

        # 清理
        if os.path.exists(db_path):
            os.unlink(db_path)

    def test_database_init(self, temp_db):
        """测试数据库初始化"""
        assert temp_db.db_path.exists()

    def test_insert_and_fetch(self, temp_db):
        """测试插入和查询"""
        # 插入分类
        cat_id = temp_db.insert('categories', {
            'name': '测试分类',
            'color': '#ff0000',
            'icon': 'test'
        })
        assert cat_id is not None

        # 查询
        row = temp_db.fetchone("SELECT * FROM categories WHERE id = ?", (cat_id,))
        assert row is not None
        assert row['name'] == '测试分类'

    def test_default_categories(self, temp_db):
        """测试默认分类"""
        categories = temp_db.fetchall("SELECT * FROM categories")
        assert len(categories) >= 5  # 至少5个默认分类


class TestClipboardManager:
    """剪贴板管理器测试"""

    @pytest.fixture
    def setup_manager(self):
        """设置管理器"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name

        Database._instance = None
        db = Database(db_path)

        from clipboard.manager import ClipboardManager
        manager = ClipboardManager(db)

        yield manager

        if os.path.exists(db_path):
            os.unlink(db_path)

    def test_auto_detect_category_code(self, setup_manager):
        """测试代码分类检测"""
        manager = setup_manager

        # 代码内容
        cat_id = manager.auto_detect_category("def hello():\n    pass", ContentType.TEXT)
        assert cat_id is not None

    def test_auto_detect_category_link(self, setup_manager):
        """测试链接分类检测"""
        manager = setup_manager

        cat_id = manager.auto_detect_category("https://example.com", ContentType.TEXT)
        assert cat_id is not None

    def test_save_item(self, setup_manager):
        """测试保存项"""
        manager = setup_manager

        item = ClipboardItem(
            content="test content",
            content_type=ContentType.TEXT,
            preview="test content",
            hash=ClipboardItem.generate_hash("test content", ContentType.TEXT)
        )

        item_id = manager.save_item(item)
        assert item_id is not None

        # 验证保存
        items = manager.get_items(limit=10)
        assert len(items) > 0
        assert items[0].content == "test content"

    def test_search(self, setup_manager):
        """测试搜索"""
        manager = setup_manager

        # 保存测试数据
        for i in range(3):
            item = ClipboardItem(
                content=f"test content {i}",
                content_type=ContentType.TEXT,
                preview=f"test content {i}",
                hash=ClipboardItem.generate_hash(f"test content {i}", ContentType.TEXT)
            )
            manager.save_item(item)

        # 搜索
        results = manager.search("test")
        assert len(results) >= 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
