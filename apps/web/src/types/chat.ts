export type MessageRole = 'user' | 'assistant' | 'system';

export type AttachmentKind = 'image' | 'video';

export interface Attachment {
  kind: AttachmentKind;
  url: string;
  asset_id?: string;
}

export type GenerationStatus = 'pending' | 'processing' | 'done' | 'failed';

export interface GenerationState {
  status: GenerationStatus;
  kind: AttachmentKind;
  url?: string;
  progress?: number;
  task_id?: string;
}

export interface Message {
  id: string;
  role: MessageRole;
  content: string;
  attachments?: Attachment[];
  generation?: GenerationState;
  feedback: 'none' | 'like' | 'dislike' | 'adjust_tone';
  created_at: string;
}
