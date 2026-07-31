"""全局异常处理：将 AppError 渲染为 {code, message, params} 统一结构。"""
from __future__ import annotations

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.error_codes import AppError, ERROR_DEFINITIONS


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
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.code.value, "message": message, "params": exc.params},
    )


async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """422 校验错误：保留 FastAPI 默认 detail 结构，供前端逐项展示。"""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"code": "VALIDATION_ERROR", "message": "Validation failed", "params": exc.errors()},
    )
