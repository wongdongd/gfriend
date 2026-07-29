"""Stripe 支付适配器实现。

对应实现方案第 8 节：国际市场首选 Stripe，使用 Stripe Checkout 与 Billing。
订阅的创建、续费、取消、扣款失败和退款均以服务商签名 Webhook 为准。
"""
from __future__ import annotations

from provider_adapters.payment.base import (
    CheckoutRequest,
    CheckoutResult,
    PaymentAdapter,
    WebhookResult,
)


class StripePaymentAdapter(PaymentAdapter):
    """Stripe 支付适配器。"""

    def __init__(self, secret_key: str, webhook_secret: str) -> None:
        import stripe

        stripe.api_key = secret_key
        self._stripe = stripe
        self._webhook_secret = webhook_secret

    @property
    def provider_name(self) -> str:
        return "stripe"

    async def create_checkout(self, request: CheckoutRequest) -> CheckoutResult:
        params: dict = {
            "mode": "subscription" if request.order_type == "subscription" else "payment",
            "success_url": request.success_url,
            "cancel_url": request.cancel_url,
            "client_reference_id": request.user_id,
            "metadata": {**request.metadata, "user_id": request.user_id, "order_type": request.order_type},
        }
        if request.email:
            params["customer_email"] = request.email

        if request.order_type == "subscription":
            params["line_items"] = [{"price": request.price_id, "quantity": 1}]
        else:
            params["line_items"] = [{"price": request.price_id, "quantity": 1}]
            if request.credits_amount:
                params["metadata"]["credits_amount"] = str(request.credits_amount)

        session = await self._stripe.checkout.Session.create_async(**params)
        return CheckoutResult(
            checkout_id=session.id,
            checkout_url=session.url,
            provider="stripe",
        )

    async def create_customer_portal(self, customer_id: str, return_url: str) -> str:
        session = await self._stripe.billing_portal.Session.create_async(
            customer=customer_id,
            return_url=return_url,
        )
        return session.url

    def handle_webhook(self, payload: bytes, headers: dict) -> WebhookResult:
        import stripe

        event = stripe.Webhook.construct_event(
            payload,
            headers.get("stripe-signature", ""),
            self._webhook_secret,
        )
        event_id = event["id"]
        event_type = event["type"]
        obj = event["data"]["object"]

        return WebhookResult(
            event_id=event_id,
            event_type=event_type,
            user_id=obj.get("client_reference_id") or obj.get("metadata", {}).get("user_id"),
            order_id=obj.get("metadata", {}).get("order_id"),
            subscription_id=obj.get("subscription") if event_type.startswith("checkout") else obj.get("id"),
            customer_id=obj.get("customer"),
            payment_id=obj.get("payment_intent"),
            amount=obj.get("amount_total") or obj.get("amount"),
            currency=obj.get("currency"),
            status=obj.get("status"),
            raw=event,
        )

    async def cancel_subscription(self, subscription_id: str) -> bool:
        sub = await self._stripe.Subscription.modify_async(
            subscription_id,
            cancel_at_period_end=True,
        )
        return bool(sub.cancel_at_period_end)

    async def refund_payment(self, payment_id: str, amount: int | None = None) -> bool:
        params: dict = {"payment_intent": payment_id}
        if amount is not None:
            params["amount"] = amount
        refund = await self._stripe.Refund.create_async(**params)
        return refund.status in ("succeeded", "pending")
