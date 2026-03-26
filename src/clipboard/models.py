"""剪贴板数据模型"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum
import hashlib
import json


class ContentType(Enum):
    """内容类型"""
    TEXT = "text"
    IMAGE = "image"
    HTML = "html"
    FILE = "file"


@dataclass
class ClipboardItem:
    """剪贴板项数据类"""
    id: Optional[int] = None
    category_id: Optional[int] = None
    content: str = ""
    content_type: ContentType = ContentType.TEXT
    preview: str = ""
    hash: str = ""
    is_favorite: bool = False
    is_deleted: bool = False
    copy_count: int = 1
    source_app: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def from_db_row(cls, row: dict) -> 'ClipboardItem':
        """从数据库行创建实例"""
        return cls(
            id=row.get('id'),
            category_id=row.get('category_id'),
            content=row.get('content', ''),
            content_type=ContentType(row.get('content_type', 'text')),
            preview=row.get('preview', ''),
            hash=row.get('hash', ''),
            is_favorite=bool(row.get('is_favorite', 0)),
            is_deleted=bool(row.get('is_deleted', 0)),
            copy_count=row.get('copy_count', 1),
            source_app=row.get('source_app', ''),
            metadata=json.loads(row.get('metadata') or '{}'),
            created_at=cls._parse_datetime(row.get('created_at')),
            updated_at=cls._parse_datetime(row.get('updated_at')),
        )

    @staticmethod
    def _parse_datetime(value: str) -> Optional[datetime]:
        """解析日期时间"""
        if not value:
            return None
        try:
            return datetime.fromisoformat(value.replace('Z', '+00:00'))
        except (ValueError, TypeError):
            return None

    @staticmethod
    def generate_hash(content: str, content_type: ContentType) -> str:
        """生成内容哈希"""
        data = f"{content_type.value}:{content}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'id': self.id,
            'category_id': self.category_id,
            'content': self.content,
            'content_type': self.content_type.value,
            'preview': self.preview,
            'hash': self.hash,
            'is_favorite': self.is_favorite,
            'is_deleted': self.is_deleted,
            'copy_count': self.copy_count,
            'source_app': self.source_app,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


@dataclass
class Category:
    """分类数据类"""
    id: Optional[int] = None
    name: str = ""
    color: str = "#3498db"
    icon: str = "folder"
    sort_order: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def from_db_row(cls, row: dict) -> 'Category':
        """从数据库行创建实例"""
        return cls(
            id=row.get('id'),
            name=row.get('name', ''),
            color=row.get('color', '#3498db'),
            icon=row.get('icon', 'folder'),
            sort_order=row.get('sort_order', 0),
            created_at=cls._parse_datetime(row.get('created_at')),
            updated_at=cls._parse_datetime(row.get('updated_at')),
        )

    @staticmethod
    def _parse_datetime(value: str) -> Optional[datetime]:
        """解析日期时间"""
        if not value:
            return None
        try:
            return datetime.fromisoformat(value.replace('Z', '+00:00'))
        except (ValueError, TypeError):
            return None

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'color': self.color,
            'icon': self.icon,
            'sort_order': self.sort_order,
        }
