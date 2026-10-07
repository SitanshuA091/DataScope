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
