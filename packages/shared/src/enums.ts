/** 状态与类型枚举 —— 与后端 SQLAlchemy 模型保持一致 */

// ===== 用户 =====
export enum AgeStatus {
  UNCONFIRMED = 'unconfirmed',
  CONFIRMED = 'confirmed',
  MINOR = 'minor',
}

export enum UserRole {
  USER = 'user',
  ADMIN = 'admin',
  OPERATOR = 'operator',
}

export enum AuthProvider {
  EMAIL = 'email',
  GOOGLE = 'google',
  FACEBOOK = 'facebook',
}

// ===== 角色 =====
export enum CharacterStatus {
  ACTIVE = 'active',
  PAUSED = 'paused',
  ARCHIVED = 'archived',
  DELETED = 'deleted',
}

// ===== 模板 =====
export enum TemplateType {
  RELATIONSHIP = 'relationship',
  PERSONALITY = 'personality',
  SCENE = 'scene',
  STYLE = 'style',
}

// ===== 消息 =====
export enum MessageRole {
  USER = 'user',
  ASSISTANT = 'assistant',
  SYSTEM = 'system',
}

export enum MessageFeedback {
  NONE = 'none',
  LIKE = 'like',
  DISLIKE = 'dislike',
  ADJUST_TONE = 'adjust_tone',
}

export enum SafetyStatus {
  PENDING = 'pending',
  PASS = 'pass',
  FLAGGED = 'flagged',
  BLOCKED = 'blocked',
  REVIEWING = 'reviewing',
}

// ===== 记忆 =====
export enum MemoryType {
  PREFERENCE = 'preference',
  EVENT = 'event',
  RELATIONSHIP = 'relationship',
  IMPORTANT_DATE = 'important_date',
  FACT = 'fact',
}

export enum MemoryStatus {
  CANDIDATE = 'candidate',
  CONFIRMED = 'confirmed',
  REJECTED = 'rejected',
  ARCHIVED = 'archived',
}

// ===== 生成任务 =====
export enum TaskType {
  IMAGE = 'image',
  VIDEO = 'video',
}

export enum TaskStatus {
  PENDING = 'pending',
  QUEUED = 'queued',
  RUNNING = 'running',
  SUCCESS = 'success',
  FAILED = 'failed',
  CANCELLED = 'cancelled',
  SAFETY_BLOCKED = 'safety_blocked',
}

// ===== 素材 =====
export enum AssetType {
  REFERENCE_IMAGE = 'reference_image',
  GENERATED_IMAGE = 'generated_image',
  GENERATED_VIDEO = 'generated_video',
  THUMBNAIL = 'thumbnail',
  EXPORT = 'export',
}

// ===== 计费 =====
export enum CreditEntryType {
  GRANT = 'grant',
  PURCHASE = 'purchase',
  SUBSCRIPTION = 'subscription',
  FREEZE = 'freeze',
  CONSUME = 'consume',
  REFUND = 'refund',
  ADJUST = 'adjust',
}

export enum OrderType {
  SUBSCRIPTION = 'subscription',
  CREDITS = 'credits',
}

export enum OrderStatus {
  PENDING = 'pending',
  PAID = 'paid',
  FAILED = 'failed',
  REFUNDED = 'refunded',
  CANCELLED = 'cancelled',
}

export enum PaymentChannel {
  STRIPE = 'stripe',
  WECHAT = 'wechat',
  ALIPAY = 'alipay',
}

export enum SubscriptionStatus {
  ACTIVE = 'active',
  TRIALING = 'trialing',
  PAST_DUE = 'past_due',
  CANCELLED = 'cancelled',
  EXPIRED = 'expired',
}

// ===== 安全 =====
export enum RiskType {
  SPAM = 'spam',
  HARASSMENT = 'harassment',
  HATE = 'hate',
  SEXUAL = 'sexual',
  VIOLENCE = 'violence',
  SELF_HARM = 'self_harm',
  CRISIS = 'crisis',
  MINOR_SAFETY = 'minor_safety',
  COPYRIGHT = 'copyright',
  OTHER = 'other',
}

export enum DispositionStatus {
  PENDING = 'pending',
  REVIEWING = 'reviewing',
  RESOLVED = 'resolved',
  ACTIONED = 'actioned',
  ESCALATED = 'escalated',
}
