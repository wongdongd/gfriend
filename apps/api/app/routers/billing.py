"""计费路由：套餐、订单、支付结账、Webhook、积分流水。"""
from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from db.models.billing import CreditEntryType, CreditLedger, Order, OrderType, PaymentChannel
from db.models.user import User
from shared.database import get_db

router = APIRouter()


class CheckoutRequest(BaseModel):
    order_type: str = "subscription"  # subscription / credits
    sku_code: str
    success_url: Optional[str] = None
    cancel_url: Optional[str] = None


@router.get("/billing/entitlements")
async def get_entitlements(user: User = Depends(get_current_user)):
    """获取当前用户的权益与积分余额。"""
    return {
        "subscription_tier": user.subscription_tier or "free",
        "credits_balance": user.credits_balance,
    }


@router.post("/billing/checkout")
async def create_checkout(req: CheckoutRequest, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """创建第三方托管支付结账会话。"""
    from provider_adapters.payment import get_payment_adapter
    from shared.config import settings

    adapter = get_payment_adapter("stripe")
    from provider_adapters.payment.base import CheckoutRequest as ProviderCheckoutRequest

    # 创建本地订单
    order = Order(
        user_id=user.id,
        type=OrderType.SUBSCRIPTION if req.order_type == "subscription" else OrderType.CREDITS,
        amount=0,  # 由服务商决定
        currency="usd",
        sku_code=req.sku_code,
        channel=PaymentChannel.STRIPE,
    )
    db.add(order)
    await db.flush()

    price_id = settings.stripe_price_subscription if req.order_type == "subscription" else settings.stripe_price_credits
    checkout_req = ProviderCheckoutRequest(
        user_id=str(user.id),
        email=user.email,
        price_id=price_id,
        order_type=req.order_type,
        success_url=req.success_url or settings.stripe_success_url,
        cancel_url=req.cancel_url or settings.stripe_cancel_url,
        metadata={"order_id": str(order.id)},
    )
    result = await adapter.create_checkout(checkout_req)
    order.provider_checkout_id = result.checkout_id
    await db.commit()

    return {"checkout_url": result.checkout_url, "order_id": str(order.id)}


@router.post("/billing/portal")
async def create_portal(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """跳转至第三方订阅管理门户。"""
    from provider_adapters.payment import get_payment_adapter
    from shared.config import settings

    # 查找用户的 stripe customer id
    result = await db.execute(
        select(Order).where(Order.user_id == user.id, Order.provider_payment_id.isnot(None)).order_by(Order.created_at.desc()).limit(1)
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未找到订阅记录")

    adapter = get_payment_adapter("stripe")
    url = await adapter.create_customer_portal(order.provider_payment_id or "", settings.app_url)
    return {"portal_url": url}


@router.post("/payments/{provider}/webhook")
async def payment_webhook(provider: str, request: Request, db: AsyncSession = Depends(get_db)):
    """验签并处理支付回调（幂等）。"""
    from provider_adapters.payment import get_payment_adapter

    if provider != "stripe":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="不支持的支付渠道")
    adapter = get_payment_adapter("stripe")
    payload = await request.body()
    headers = dict(request.headers)
    try:
        result = adapter.handle_webhook(payload, headers)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"验签失败: {e}")

    # 幂等检查：按 event_id 去重
    existing = await db.execute(select(Order).where(Order.provider_event_id == result.event_id))
    if existing.scalar_one_or_none():
        return {"ok": True, "duplicate": True}

    # 根据事件类型更新订单/订阅/积分
    if result.event_type == "checkout.session.completed":
        user_id = uuid.UUID(result.user_id) if result.user_id else None
        if user_id:
            # 查找订单并更新
            order_result = await db.execute(
                select(Order).where(Order.provider_checkout_id == result.order_id or "")
            )
            order = order_result.scalar_one_or_none()
            if order:
                from db.models.billing import OrderStatus
                order.status = OrderStatus.PAID
                order.provider_payment_id = result.payment_id
                order.provider_event_id = result.event_id
                # 积分包：发放积分
                if order.type == OrderType.CREDITS and order.credits_amount:
                    user_result = await db.execute(select(User).where(User.id == user_id))
                    u = user_result.scalar_one_or_none()
                    if u:
                        u.credits_balance += order.credits_amount
                        ledger = CreditLedger(
                            user_id=u.id,
                            type=CreditEntryType.PURCHASE,
                            amount=order.credits_amount,
                            balance_after=u.credits_balance,
                            order_id=order.id,
                        )
                        db.add(ledger)
    await db.commit()
    return {"ok": True}


@router.get("/billing/credits/ledger")
async def list_credit_ledger(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db), limit: int = 50):
    """获取积分消费流水。"""
    result = await db.execute(
        select(CreditLedger).where(CreditLedger.user_id == user.id).order_by(CreditLedger.created_at.desc()).limit(limit)
    )
    return {
        "items": [
            {
                "id": str(l.id),
                "type": l.type.value,
                "amount": l.amount,
                "balance_after": l.balance_after,
                "note": l.note,
                "created_at": l.created_at.isoformat(),
            }
            for l in result.scalars().all()
        ]
    }
