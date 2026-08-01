"""全局异常处理：将 AppError 渲染为 {code, message, params} 统一结构。"""
from __future__ import annotations

import logging

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

# Starlette 重命名了 422 常量：新版本用 UNPROCESSABLE_CONTENT，旧版本用 UNPROCESSABLE_ENTITY。
# 兼容两种版本，避免 AttributeError 与弃用警告。
HTTP_422 = getattr(
    status,
    "HTTP_422_UNPROCESSABLE_CONTENT",
    status.HTTP_422_UNPROCESSABLE_ENTITY,
)

from api.core.error_codes import AppError, ERROR_DEFINITIONS

logger = logging.getLogger(__name__)


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """业务异常 → 统一 JSON（code 稳定、message 默认英文，前端按 locale 翻译）。"""
    _status, default_message = ERROR_DEFINITIONS[exc.code]
    message = default_message
    if exc.params:
        try:
            message = default_message.format(**exc.params)
        except (KeyError, IndexError):
            # 参数缺失时回退到未渲染模板，保证可读
            pass
    # 4xx 记 WARNING，5xx 记 ERROR，方便排查
    log_level = logging.ERROR if exc.status_code >= 500 else logging.WARNING
    logger.log(
        log_level,
        "%s %s → %d %s: %s",
        request.method,
        request.url.path,
        exc.status_code,
        exc.code.value,
        message,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.code.value, "message": message, "params": exc.params},
    )


async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """422 校验错误：保留 FastAPI 默认 detail 结构，供前端逐项展示。"""
    return JSONResponse(
        status_code=HTTP_422,
        content={"code": "VALIDATION_ERROR", "message": "Validation failed", "params": exc.errors()},
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """兜底：所有未捕获异常 → 500 + 统一 JSON，并记录完整堆栈到日志。"""
    logger.exception("Unhandled exception on %s %s: %s", request.method, request.url.path, exc)
    return JSONResponse(
        status_code=500,
        content={
            "code": "UNKNOWN",
            "message": "Internal server error",
            "params": {},
        },
    )
