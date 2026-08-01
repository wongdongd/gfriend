"""支付适配器工厂。"""
from __future__ import annotations

from provider_adapters.payment.base import (
  CheckoutRequest,
  CheckoutResult,
  PaymentAdapter,
  WebhookResult,
)


def get_payment_adapter(channel: str = "stripe") -> PaymentAdapter:
  """根据渠道创建支付适配器。"""
  from shared.config import settings

  if channel == "stripe" and settings.stripe_secret_key:
    from provider_adapters.payment.stripe_adapter import StripePaymentAdapter

    return StripePaymentAdapter(
      secret_key=settings.stripe_secret_key,
      webhook_secret=settings.stripe_webhook_secret,
    )
  # 本地渠道可在此扩展（wechat / alipay）
  raise ValueError(f"未配置支付渠道: {channel}；请在 .env 中设置 STRIPE_SECRET_KEY")


__all__ = [
  "PaymentAdapter",
  "CheckoutRequest",
  "CheckoutResult",
  "WebhookResult",
  "get_payment_adapter",
]
