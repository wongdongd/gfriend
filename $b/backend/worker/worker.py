"""Celery Worker 入口。

启动：
    celery -A app.worker worker -l info
    celery -A app.worker worker -Q image,celery -l info   # 图片队列
    celery -A app.worker worker -Q video -l info --concurrency=2  # 视频队列（低并发）
"""
from app.celery_app import app

__all__ = ["app"]
