"""支付适配器抽象基类。

对应实现方案第 8 节：
- 支付不直接处理或保存银行卡信息；后端创建第三方支付服务商提供的结账会话。
- 支付 Webhook 必须验证服务商签名、记录事件 ID 并按事件 ID 幂等处理。
- 建议适配器接口：createCheckout / createCustomerPortal / handleWebhook / cancelSubscription / refundPayment。
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class CheckoutRequest:
    """创建结账会话请求。"""

    user_id: str
    email: str | None = None
    # SKU 标识（Stripe price_id 或本地渠道商品码）
    price_id: str = ""
    # 积分包数量
    credits_amount: int | None = None
    # 订单类型：subscription / credits
    order_type: str = "subscription"
    success_url: str = ""
    cancel_url: str = ""
    # 透传元数据
    metadata: dict = field(default_factory=dict)


@dataclass
class CheckoutResult:
    """结账会话创建结果。"""

    checkout_id: str  # 供应商会话 ID
    checkout_url: str  # 用户跳转的托管收银台 URL
    provider: str


@dataclass
class WebhookResult:
    """Webhook 处理结果。"""

    event_id: str  # 供应商事件 ID（用于幂等）
    event_type: str  # 事件类型（如 checkout.session.completed）
    # 解析后的标准化数据
    user_id: str | None = None
    order_id: str | None = None
    subscription_id: str | None = None
    customer_id: str | None = None
    payment_id: str | None = None
    amount: int | None = None
    currency: str | None = None
    status: str | None = None
    raw: dict = field(default_factory=dict)


class PaymentAdapter(ABC):
    """支付适配器抽象基类。"""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """渠道标识。"""

    @abstractmethod
    async def create_checkout(self, request: CheckoutRequest) -> CheckoutResult:
        """创建第三方托管支付结账会话。"""

    @abstractmethod
    async def create_customer_portal(self, customer_id: str, return_url: str) -> str:
        """跳转至第三方订阅/账单管理门户，返回 URL。"""

    @abstractmethod
    def handle_webhook(self, payload: bytes, headers: dict) -> WebhookResult:
        """验签并处理支付回调，返回标准化结果。"""

    @abstractmethod
    async def cancel_subscription(self, subscription_id: str) -> bool:
        """取消订阅。"""

    @abstractmethod
    async def refund_payment(self, payment_id: str, amount: int | None = None) -> bool:
        """退款。"""
