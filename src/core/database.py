"""数据库管理模块"""

import sqlite3
from pathlib import Path
from typing import Optional, List, Any
from contextlib import contextmanager
from loguru import logger


class Database:
    """SQLite数据库管理类（单例模式）"""

    _instance: Optional['Database'] = None

    def __new__(cls, db_path: str = None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, db_path: str = None):
        if self._initialized:
            return

        self.db_path = Path(db_path or self._get_default_path())
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
        self._initialized = True
        logger.info(f"数据库初始化完成: {self.db_path}")

    @staticmethod
    def _get_default_path() -> str:
        """获取默认数据库路径（跨平台）"""
        import platform
        import os

        system = platform.system()
        if system == "Windows":
            base = Path(os.environ.get('APPDATA', Path.home()))
        else:  # Linux/macOS
            base = Path.home() / '.local' / 'share'

        return str(base / 'work-assistant' / 'data' / 'work_assistant.db')

    @contextmanager
    def get_connection(self):
        """获取数据库连接的上下文管理器"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"数据库错误: {e}")
            raise
        finally:
            conn.close()

    def execute(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        """执行SQL语句"""
        with self.get_connection() as conn:
            return conn.execute(sql, params)

    def fetchone(self, sql: str, params: tuple = ()) -> Optional[dict]:
        """查询单条记录"""
        with self.get_connection() as conn:
            cursor = conn.execute(sql, params)
            row = cursor.fetchone()
            return dict(row) if row else None

    def fetchall(self, sql: str, params: tuple = ()) -> List[dict]:
        """查询多条记录"""
        with self.get_connection() as conn:
            cursor = conn.execute(sql, params)
            return [dict(row) for row in cursor.fetchall()]

    def insert(self, table: str, data: dict) -> int:
        """插入记录并返回ID"""
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['?' for _ in data])
        sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"

        with self.get_connection() as conn:
            cursor = conn.execute(sql, tuple(data.values()))
            return cursor.lastrowid

    def update(self, table: str, data: dict, where: str, where_params: tuple = ()) -> int:
        """更新记录"""
        set_clause = ', '.join([f"{k} = ?" for k in data.keys()])
        sql = f"UPDATE {table} SET {set_clause} WHERE {where}"

        with self.get_connection() as conn:
            cursor = conn.execute(sql, tuple(data.values()) + where_params)
            return cursor.rowcount

    def delete(self, table: str, where: str, where_params: tuple = ()) -> int:
        """删除记录"""
        sql = f"DELETE FROM {table} WHERE {where}"
        with self.get_connection() as conn:
            cursor = conn.execute(sql, where_params)
            return cursor.rowcount

    def _init_database(self):
        """初始化数据库表结构"""
        with self.get_connection() as conn:
            # 分类表
            conn.execute('''
                CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    color TEXT DEFAULT '#3498db',
                    icon TEXT DEFAULT 'folder',
                    sort_order INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # 剪贴板项表
            conn.execute('''
                CREATE TABLE IF NOT EXISTS clipboard_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category_id INTEGER,
                    content TEXT NOT NULL,
                    content_type TEXT NOT NULL,
                    preview TEXT,
                    hash TEXT UNIQUE,
                    is_favorite INTEGER DEFAULT 0,
                    is_deleted INTEGER DEFAULT 0,
                    copy_count INTEGER DEFAULT 1,
                    source_app TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (category_id) REFERENCES categories(id)
                )
            ''')

            # 提醒表
            conn.execute('''
                CREATE TABLE IF NOT EXISTS reminders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    content TEXT,
                    reminder_type TEXT NOT NULL,
                    trigger_time TIMESTAMP,
                    interval_value INTEGER,
                    interval_unit TEXT,
                    is_recurring INTEGER DEFAULT 0,
                    is_enabled INTEGER DEFAULT 1,
                    next_trigger TIMESTAMP,
                    sound_enabled INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # 提醒日志表
            conn.execute('''
                CREATE TABLE IF NOT EXISTS reminder_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    reminder_id INTEGER,
                    triggered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'triggered',
                    FOREIGN KEY (reminder_id) REFERENCES reminders(id)
                )
            ''')

            # 创建索引
            conn.execute('CREATE INDEX IF NOT EXISTS idx_clipboard_category ON clipboard_items(category_id)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_clipboard_created ON clipboard_items(created_at DESC)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_clipboard_hash ON clipboard_items(hash)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_reminder_next_trigger ON reminders(next_trigger)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_reminder_enabled ON reminders(is_enabled)')

            # 插入默认分类
            default_categories = [
                ('默认', '#95a5a6', 'folder', 0),
                ('代码', '#3498db', 'code', 1),
                ('文本', '#2ecc71', 'text', 2),
                ('链接', '#9b59b6', 'link', 3),
                ('图片', '#e74c3c', 'image', 4),
            ]

            for name, color, icon, sort_order in default_categories:
                try:
                    conn.execute(
                        "INSERT OR IGNORE INTO categories (name, color, icon, sort_order) VALUES (?, ?, ?, ?)",
                        (name, color, icon, sort_order)
                    )
                except sqlite3.IntegrityError:
                    pass  # 已存在，忽略
