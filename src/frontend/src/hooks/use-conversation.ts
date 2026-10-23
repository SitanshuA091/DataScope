"use client";

import { useCallback, useEffect, useState } from "react";
import { apiFetch } from "@/lib/api-client";
import type {
  ChatResponse,
  Message,
  MessageListResponse,
  QuestionUsage,
} from "@/types/conversation";

export function useConversation(datasetId: string | null | undefined) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [usage, setUsage] = useState<QuestionUsage | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    if (!datasetId) {
      setMessages([]);
      setUsage(null);
      setError(null);
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const [messageResponse, usageResponse] = await Promise.all([
        apiFetch<MessageListResponse>(`/datasets/${datasetId}/messages`),
        apiFetch<QuestionUsage>(`/datasets/${datasetId}/question-usage`),
      ]);
      setMessages(messageResponse.messages);
      setUsage(usageResponse);
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Unable to load conversation.",
      );
    } finally {
      setIsLoading(false);
    }
  }, [datasetId]);

  useEffect(() => {
    void Promise.resolve().then(refresh);
  }, [refresh]);

  const sendChat = useCallback(
    async (content: string, activeColumns?: string[]) => {
      if (!datasetId) {
        throw new Error("A dataset is required before chatting.");
      }

      setIsSending(true);
      setError(null);

      const optimisticUserMessage: Message = {
        id: `optimistic-${Date.now()}`,
        conversation_id: usage?.conversation_id ?? "pending",
        role: "user",
        content: content.trim(),
        analysis_run_id: null,
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, optimisticUserMessage]);

      try {
        const response = await apiFetch<ChatResponse>(`/datasets/${datasetId}/chat`, {
          method: "POST",
          body: {
            content: content.trim(),
            active_columns: activeColumns,
          },
        });
        await refresh();
        return response;
      } catch (requestError) {
        setMessages((prev) =>
          prev.filter((msg) => msg.id !== optimisticUserMessage.id),
        );
        const errorMessage =
          requestError instanceof Error
            ? requestError.message
            : "Failed to send chat message.";
        setError(errorMessage);
        throw requestError;
      } finally {
        setIsSending(false);
      }
    },
    [datasetId, refresh, usage?.conversation_id],
  );

  const saveMessage = useCallback(
    async ({
      role,
      content,
      analysisRunId,
    }: {
      role: "user" | "assistant" | "system";
      content: string;
      analysisRunId?: string | null;
    }) => {
      if (!datasetId) {
        throw new Error("A dataset is required before saving messages.");
      }

      const message = await apiFetch<Message>(`/datasets/${datasetId}/messages`, {
        method: "POST",
        body: {
          role,
          content,
          analysis_run_id: analysisRunId ?? null,
        },
      });
      await refresh();
      return message;
    },
    [datasetId, refresh],
  );

  return {
    messages,
    usage,
    isLoading,
    isSending,
    error,
    refresh,
    saveMessage,
    sendChat,
  };
}
