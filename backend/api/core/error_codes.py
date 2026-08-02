"""统一错误码体系。

设计目标（国际化）：
- 后端只下发稳定的英文 `code` + 默认英文 `message`，不向客户端暴露中文文案。
- 前端按当前 locale 将 `code` 翻译成用户语言（见 web 端 error-codes.ts）。
- HTTP 状态码由错误码定义决定，避免散落的魔法数字。

约定：
- `ErrorCode` 为 StrEnum，值即下发到前端的 `code` 字符串。
- `ERROR_DEFINITIONS[code] = (http_status, default_message)`，default_message 为英文模板，
  可含 `{param}` 占位符，由 error_handlers 用 params 渲染。
"""
from __future__ import annotations

from enum import StrEnum


class ErrorCode(StrEnum):
    # 认证 / 令牌
    AUTH_TOKEN_MISSING = "AUTH_TOKEN_MISSING"
    AUTH_TOKEN_INVALID = "AUTH_TOKEN_INVALID"
    AUTH_TOKEN_PAYLOAD_INVALID = "AUTH_TOKEN_PAYLOAD_INVALID"
    AUTH_USER_INVALID = "AUTH_USER_INVALID"
    AUTH_EMAIL_TAKEN = "AUTH_EMAIL_TAKEN"
    AUTH_INVALID_CREDENTIALS = "AUTH_INVALID_CREDENTIALS"
    AUTH_ACCOUNT_DISABLED = "AUTH_ACCOUNT_DISABLED"
    AUTH_REFRESH_INVALID = "AUTH_REFRESH_INVALID"

    # 权限
    PERMISSION_ADMIN_REQUIRED = "PERMISSION_ADMIN_REQUIRED"
    PERMISSION_OPERATOR_REQUIRED = "PERMISSION_OPERATOR_REQUIRED"

    # 资源不存在
    RESOURCE_CHARACTER_NOT_FOUND = "RESOURCE_CHARACTER_NOT_FOUND"
    RESOURCE_MEMORY_NOT_FOUND = "RESOURCE_MEMORY_NOT_FOUND"
    RESOURCE_MESSAGE_NOT_FOUND = "RESOURCE_MESSAGE_NOT_FOUND"
    RESOURCE_TASK_NOT_FOUND = "RESOURCE_TASK_NOT_FOUND"
    RESOURCE_ASSET_NOT_FOUND = "RESOURCE_ASSET_NOT_FOUND"

    # 业务校验
    BILLING_INSUFFICIENT_CREDITS = "BILLING_INSUFFICIENT_CREDITS"
    TASK_CANNOT_CANCEL = "TASK_CANNOT_CANCEL"
    FEEDBACK_INVALID_TYPE = "FEEDBACK_INVALID_TYPE"
    BILLING_SUBSCRIPTION_NOT_FOUND = "BILLING_SUBSCRIPTION_NOT_FOUND"
    BILLING_UNSUPPORTED_CHANNEL = "BILLING_UNSUPPORTED_CHANNEL"
    BILLING_SIGNATURE_FAILED = "BILLING_SIGNATURE_FAILED"
    BILLING_CHECKOUT_FAILED = "BILLING_CHECKOUT_FAILED"
    ASSET_BLOCKED = "ASSET_BLOCKED"


# (http_status, default_message)
ERROR_DEFINITIONS: dict[ErrorCode, tuple[int, str]] = {
    ErrorCode.AUTH_TOKEN_MISSING: (401, "Authentication token is missing"),
    ErrorCode.AUTH_TOKEN_INVALID: (401, "Token is invalid or expired"),
    ErrorCode.AUTH_TOKEN_PAYLOAD_INVALID: (401, "Token payload is invalid"),
    ErrorCode.AUTH_USER_INVALID: (401, "User is invalid or disabled"),
    ErrorCode.AUTH_EMAIL_TAKEN: (409, "This email is already registered"),
    ErrorCode.AUTH_INVALID_CREDENTIALS: (401, "Incorrect email or password"),
    ErrorCode.AUTH_ACCOUNT_DISABLED: (403, "This account has been disabled"),
    ErrorCode.AUTH_REFRESH_INVALID: (401, "Refresh token is invalid"),

    ErrorCode.PERMISSION_ADMIN_REQUIRED: (403, "Admin permission required"),
    ErrorCode.PERMISSION_OPERATOR_REQUIRED: (403, "Operator permission required"),

    ErrorCode.RESOURCE_CHARACTER_NOT_FOUND: (404, "Character not found"),
    ErrorCode.RESOURCE_MEMORY_NOT_FOUND: (404, "Memory not found"),
    ErrorCode.RESOURCE_MESSAGE_NOT_FOUND: (404, "Message not found"),
    ErrorCode.RESOURCE_TASK_NOT_FOUND: (404, "Task not found"),
    ErrorCode.RESOURCE_ASSET_NOT_FOUND: (404, "Asset not found"),

    ErrorCode.BILLING_INSUFFICIENT_CREDITS: (402, "Insufficient credits"),
    ErrorCode.TASK_CANNOT_CANCEL: (400, "This task can no longer be cancelled"),
    ErrorCode.FEEDBACK_INVALID_TYPE: (400, "Invalid feedback type"),
    ErrorCode.BILLING_SUBSCRIPTION_NOT_FOUND: (404, "Subscription not found"),
    ErrorCode.BILLING_UNSUPPORTED_CHANNEL: (400, "Unsupported payment channel"),
    ErrorCode.BILLING_SIGNATURE_FAILED: (400, "Payment signature verification failed: {reason}"),
    ErrorCode.BILLING_CHECKOUT_FAILED: (502, "Payment provider checkout creation failed: {reason}"),
    ErrorCode.ASSET_BLOCKED: (403, "This asset has been blocked"),
}


class AppError(Exception):
    """业务异常：携带稳定的错误码与可选参数，由全局 handler 渲染为 JSON。"""

    def __init__(self, code: ErrorCode, params: dict | None = None):
        self.code = code
        self.params: dict = params or {}
        status_code, default_message = ERROR_DEFINITIONS[code]
        self.status_code = status_code
        self.message = default_message
        super().__init__(default_message)
