#!/usr/bin/env python3
"""Work Assistant - 工作助手

一个跨平台的工作助手应用，提供剪贴板管理和定时提醒功能。
"""

import sys
from pathlib import Path

# 添加项目根目录到路径，以支持绝对导入
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.app import WorkAssistantApp


def main():
    """主入口"""
    # 配置日志
    from loguru import logger

    # 移除默认处理器
    logger.remove()

    # 添加控制台处理器
    logger.add(
        sys.stderr,
        level="DEBUG",
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )

    # 添加文件处理器
    log_path = Path.home() / ".local" / "share" / "work-assistant" / "logs"
    log_path.mkdir(parents=True, exist_ok=True)
    logger.add(
        log_path / "work_assistant.log",
        rotation="10 MB",
        retention="7 days",
        level="INFO"
    )

    logger.info("启动 Work Assistant...")

    try:
        app = WorkAssistantApp()
        sys.exit(app.run())
    except Exception as e:
        logger.exception(f"应用启动失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
