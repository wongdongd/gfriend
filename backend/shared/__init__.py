"""shared 包：配置、数据库、安全、依赖注入等通用工具。"""
from shared.config import settings
from shared.logging_config import setup_logging

# 初始化统一日志（文件滚动 + 控制台），保证 API / Worker / 迁移共用
setup_logging()

__all__ = ["settings", "setup_logging"]
