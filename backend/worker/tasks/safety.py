"""安全审核任务。"""
from __future__ import annotations

import logging

from shared.async_runner import run_async

from worker.celery_app import app

logger = logging.getLogger(__name__)


@app.task(name="worker.tasks.safety.moderate_text")
def moderate_text(text: str, context: str = "user_input") -> dict:
    """异步文本审核。"""
    from provider_adapters.safety import get_safety_adapter

    result = run_async(get_safety_adapter().check_text(text, context))
    return {"verdict": result.verdict.value, "crisis_level": result.crisis_level.value, "flagged": result.flagged_categories}


@app.task(name="worker.tasks.safety.moderate_image")
def moderate_image(object_key: str) -> dict:
    """异步图片审核。"""
    from provider_adapters.safety import get_safety_adapter

    result = run_async(get_safety_adapter().check_image(object_key))
    return {"verdict": result.verdict.value, "flagged": result.flagged_categories}
