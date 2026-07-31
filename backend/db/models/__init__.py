"""数据库模型聚合导出。

导入所有模型以便 Alembic autogenerate 与 SQLAlchemy registry 注册。
"""
from db.models.asset import Asset, AssetSource, AssetType, Work
from db.models.billing import (
    CreditEntryType,
    CreditLedger,
    Order,
    OrderStatus,
    OrderType,
    PaymentChannel,
    Subscription,
    SubscriptionStatus,
)
from db.models.character import Character, CharacterStatus
from db.models.conversation import (
    Conversation,
    Message,
    MessageFeedback,
    MessageRole,
    SafetyStatus,
)
from db.models.generation import GenerationTask, OutboxEvent, TaskStatus, TaskType
from db.models.memory import Memory, MemoryStatus, MemoryType
from db.models.safety import DispositionStatus, RiskType, SafetyEvent
from db.models.template import Template, TemplateType
from db.models.user import AgeStatus, AuthIdentity, AuthProvider, User, UserRole

__all__ = [
    # user
    "User",
    "AuthIdentity",
    "AgeStatus",
    "AuthProvider",
    "UserRole",
    # template
    "Template",
    "TemplateType",
    # character
    "Character",
    "CharacterStatus",
    # conversation
    "Conversation",
    "Message",
    "MessageRole",
    "MessageFeedback",
    "SafetyStatus",
    # memory
    "Memory",
    "MemoryType",
    "MemoryStatus",
    # asset & work
    "Asset",
    "AssetType",
    "AssetSource",
    "Work",
    # generation
    "GenerationTask",
    "TaskType",
    "TaskStatus",
    "OutboxEvent",
    # billing
    "CreditLedger",
    "CreditEntryType",
    "Order",
    "OrderType",
    "OrderStatus",
    "PaymentChannel",
    "Subscription",
    "SubscriptionStatus",
    # safety
    "SafetyEvent",
    "RiskType",
    "DispositionStatus",
]
