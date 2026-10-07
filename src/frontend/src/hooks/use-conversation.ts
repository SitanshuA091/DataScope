"use client";

import { useCallback, useEffect, useState } from "react";
import { apiFetch } from "@/lib/api-client";
import type {
  Message,
  MessageListResponse,
  QuestionUsage,
} from "@/types/conversation";

export function useConversation(datasetId: string | null | undefined) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [usage, setUsage] = useState<QuestionUsage | null>(null);
  const [isLoading, setIsLoading] = useState(false);
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

  return { messages, usage, isLoading, error, refresh, saveMessage };
}
