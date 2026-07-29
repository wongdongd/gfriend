/** 前端共享 TypeScript 类型 */

import {
  AgeStatus,
  AssetType,
  CharacterStatus,
  CreditEntryType,
  MemoryStatus,
  MemoryType,
  MessageFeedback,
  MessageRole,
  OrderStatus,
  OrderType,
  PaymentChannel,
  SafetyStatus,
  SubscriptionStatus,
  TaskStatus,
  TaskType,
  TemplateType,
  UserRole,
} from './enums';

export interface User {
  id: string;
  email: string | null;
  display_name: string | null;
  age_status: AgeStatus;
  role: UserRole;
  subscription_tier: string | null;
  credits_balance: number;
}

export interface Character {
  id: string;
  name: string;
  companion_preference: string | null;
  relationship_template_code: string | null;
  personality_template_code: string | null;
  visual_style_code: string | null;
  status: CharacterStatus;
  created_at: string;
}

export interface Template {
  id: string;
  type: TemplateType;
  code: string;
  display_config: string;
  preview_url: string | null;
}

export interface Message {
  id: string;
  role: MessageRole;
  content: string;
  feedback: MessageFeedback;
  created_at: string;
}

export interface Conversation {
  conversation_id: string | null;
  messages: Message[];
}

export interface Memory {
  id: string;
  character_id: string;
  content: string;
  type: MemoryType;
  status: MemoryStatus;
  created_at: string;
}

export interface GenerationTask {
  id: string;
  type: TaskType;
  status: TaskStatus;
  credits_cost: number;
  error_message: string | null;
  created_at: string;
  completed_at: string | null;
}

export interface Asset {
  id: string;
  object_key: string;
  type: AssetType;
}

export interface CreditLedgerEntry {
  id: string;
  type: CreditEntryType;
  amount: number;
  balance_after: number;
  note: string | null;
  created_at: string;
}

export interface Order {
  id: string;
  type: OrderType;
  status: OrderStatus;
  amount: number;
  currency: string;
  channel: PaymentChannel;
}

export interface Subscription {
  id: string;
  status: SubscriptionStatus;
  tier: string;
  current_period_end: string | null;
}

/** SSE 流式回复的事件类型 */
export type ChatStreamEvent =
  | { type: 'token'; content: string }
  | { type: 'done'; message_id: string; safety?: string; crisis?: boolean }
  | { type: 'error'; message: string };
