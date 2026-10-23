export type Conversation = {
  id: string;
  workspace_id: string;
  dataset_version_id: string;
  active_columns_json: string[];
  created_at: string;
  updated_at: string;
};

export type Message = {
  id: string;
  conversation_id: string;
  role: "user" | "assistant" | "system" | string;
  content: string;
  analysis_run_id: string | null;
  created_at: string;
};

export type MessageListResponse = {
  conversation: Conversation;
  messages: Message[];
};

export type QuestionUsage = {
  conversation_id: string;
  used: number;
  limit: number;
  remaining: number;
};

export type ChatResponse = {
  user_message: Message;
  assistant_message: Message;
  analysis_run_id: string | null;
  plan: {
    intent?: string;
    requires_clarification?: boolean;
    clarification_question?: string | null;
    tools?: Array<{
      name: string;
      arguments: Record<string, unknown>;
      reason?: string;
    }>;
  } | null;
  interpretation: {
    answer: string;
    key_findings?: string[];
    limitations?: string[];
    follow_up_questions?: string[];
  } | null;
};
