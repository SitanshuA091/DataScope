"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { useAnalysisRun } from "@/hooks/use-analysis-run";
import { useConversation } from "@/hooks/use-conversation";
import { formatDateTime } from "@/lib/formatters";

export function ChatPanel({
  datasetId,
  onSubmitted,
}: {
  datasetId: string | null;
  onSubmitted: () => void;
}) {
  const [question, setQuestion] = useState("");
  const { submitAnalysis, isSubmitting, error } = useAnalysisRun(datasetId);
  const {
    messages,
    usage,
    isLoading: isLoadingMessages,
    error: conversationError,
    saveMessage,
  } = useConversation(datasetId);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!question.trim() || !datasetId) {
      return;
    }

    const submittedQuestion = question.trim();
    const run = await submitAnalysis(
      [
        {
          name: "high_level",
          arguments: { question: submittedQuestion },
        },
      ],
      true,
    );
    await saveMessage({
      role: "user",
      content: submittedQuestion,
      analysisRunId: run.id,
    });
    setQuestion("");
    onSubmitted();
  }

  return (
    <div className="sticky bottom-0 border-t border-slate-200 bg-white p-4 shadow-[0_-8px_20px_rgba(15,23,42,0.04)]">
      <div className="mx-auto mb-3 max-w-5xl">
        {isLoadingMessages ? (
          <p className="text-xs text-slate-500">Loading conversation...</p>
        ) : messages.length > 0 ? (
          <div className="max-h-28 space-y-2 overflow-y-auto rounded-md border border-slate-200 bg-slate-50 p-3">
            {messages.slice(-3).map((message) => (
              <div
                className="flex flex-col gap-1 sm:flex-row sm:items-baseline sm:justify-between"
                key={message.id}
              >
                <p className="truncate text-sm text-slate-700">
                  <span className="font-medium text-slate-950">
                    {message.role}
                  </span>{" "}
                  {message.content}
                </p>
                <p className="shrink-0 text-xs text-slate-500">
                  {formatDateTime(message.created_at)}
                </p>
              </div>
            ))}
          </div>
        ) : null}
      </div>
      <form
        className="mx-auto flex max-w-5xl flex-col gap-3 sm:flex-row"
        onSubmit={handleSubmit}
      >
        <textarea
          className="min-h-12 flex-1 resize-none rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-950 placeholder:text-slate-400"
          disabled={!datasetId || isSubmitting}
          onChange={(event) => setQuestion(event.target.value)}
          placeholder={
            datasetId
              ? "Ask about this dataset..."
              : "Upload a dataset before asking a question."
          }
          value={question}
        />
        <Button
          className="sm:self-stretch"
          disabled={
            !datasetId ||
            isSubmitting ||
            !question.trim() ||
            usage?.remaining === 0
          }
          type="submit"
        >
          {isSubmitting ? "Sending..." : "Send"}
        </Button>
      </form>
      {usage ? (
        <p className="mx-auto mt-2 max-w-5xl text-xs text-slate-500">
          Questions used: {usage.used}/{usage.limit}
        </p>
      ) : null}
      {error ? (
        <p className="mx-auto mt-2 max-w-5xl text-sm text-red-600">{error}</p>
      ) : null}
      {conversationError ? (
        <p className="mx-auto mt-2 max-w-5xl text-sm text-red-600">
          {conversationError}
        </p>
      ) : null}
    </div>
  );
}
