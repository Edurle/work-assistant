"""配置管理模块"""

import json
from pathlib import Path
from typing import Any, Optional
from dataclasses import dataclass, field, asdict
from loguru import logger


@dataclass
class AppConfig:
    """应用配置"""
    # 窗口设置
    window_width: int = 900
    window_height: int = 650
    window_x: Optional[int] = None
    window_y: Optional[int] = None
    start_minimized: bool = False

    # 剪贴板设置
    clipboard_monitor_enabled: bool = True
    clipboard_max_items: int = 1000  # 最大保存数量
    clipboard_auto_clear_days: int = 30  # 自动清理天数

    # 提醒设置
    reminder_check_interval: int = 1000  # 检查间隔（毫秒）
    reminder_sound_enabled: bool = True
    reminder_default_sound: str = "default"

    # 通用设置
    language: str = "zh_CN"
    theme: str = "light"
    auto_start: bool = False  # 开机自启动

    # 字体设置
    clipboard_font_size: int = 10  # 剪贴板面板字体大小（pt）
    reminder_font_size: int = 10   # 提醒面板字体大小（pt）


class Config:
    """配置管理类（单例模式）"""

    _instance: Optional['Config'] = None

    def __new__(cls, config_path: str = None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, config_path: str = None):
        if self._initialized:
            return

        self.config_path = Path(config_path or self._get_default_path())
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self._config = AppConfig()
        self._load()
        self._initialized = True
        logger.info(f"配置加载完成: {self.config_path}")

    @staticmethod
    def _get_default_path() -> str:
        """获取默认配置路径（跨平台）"""
        import platform
        import os

        system = platform.system()
        if system == "Windows":
            base = Path(os.environ.get('APPDATA', Path.home()))
        else:
            base = Path.home() / '.config'

        return str(base / 'work-assistant' / 'config.json')

    @property
    def data(self) -> AppConfig:
        """获取配置数据"""
        return self._config

    def _load(self):
        """从文件加载配置"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for key, value in data.items():
                        if hasattr(self._config, key):
                            setattr(self._config, key, value)
                logger.debug("配置文件加载成功")
            except Exception as e:
                logger.warning(f"配置文件加载失败，使用默认配置: {e}")

    def save(self):
        """保存配置到文件"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(asdict(self._config), f, indent=2, ensure_ascii=False)
            logger.debug("配置文件保存成功")
        except Exception as e:
            logger.error(f"配置文件保存失败: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置项"""
        return getattr(self._config, key, default)

    def set(self, key: str, value: Any):
        """设置配置项"""
        if hasattr(self._config, key):
            setattr(self._config, key, value)
            self.save()
        else:
            logger.warning(f"未知的配置项: {key}")

    def reset(self):
        """重置为默认配置"""
        self._config = AppConfig()
        self.save()
        logger.info("配置已重置为默认值")
