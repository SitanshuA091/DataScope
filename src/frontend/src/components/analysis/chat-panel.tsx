"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { useAnalysisRun } from "@/hooks/use-analysis-run";
import { useConversation } from "@/hooks/use-conversation";
import { formatDateTime } from "@/lib/formatters";
import type { Message } from "@/types/conversation";

function ChatMessage({
  message,
  workspaceId,
}: {
  message: Message;
  workspaceId?: string;
}) {
  const isUser = message.role === "user";

  return (
    <div
      className={`rounded-lg border px-3 py-2.5 ${
        isUser ? "border-slate-200 bg-white" : "border-blue-100 bg-blue-50/50"
      }`}
    >
      <div className="flex items-baseline justify-between gap-3">
        <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
          {message.role}
        </p>
        <p className="shrink-0 text-[11px] text-slate-400">
          {formatDateTime(message.created_at)}
        </p>
      </div>
      <p className="mt-1 whitespace-pre-wrap text-sm text-slate-800">
        {message.content}
      </p>
      {message.analysis_run_id && workspaceId ? (
        <Link
          className="mt-2 inline-flex text-xs font-medium text-blue-700 hover:underline"
          href={`/workspaces/${workspaceId}/runs/${message.analysis_run_id}`}
        >
          Open analysis results →
        </Link>
      ) : null}
    </div>
  );
}

export function ChatPanel({
  datasetId,
  workspaceId,
  activeJobCount = 0,
  onSubmitted,
}: {
  datasetId: string | null;
  workspaceId?: string;
  activeJobCount?: number;
  onSubmitted: () => void;
}) {
  const router = useRouter();
  const [question, setQuestion] = useState("");
  const { submitAnalysis, isSubmitting, error } = useAnalysisRun(datasetId);
  const {
    messages,
    usage,
    isLoading: isLoadingMessages,
    error: conversationError,
    saveMessage,
  } = useConversation(datasetId);

  const atQuestionLimit = usage?.remaining === 0;
  const atJobLimit = activeJobCount >= 2;

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (
      !question.trim() ||
      !datasetId ||
      !workspaceId ||
      atQuestionLimit ||
      atJobLimit
    ) {
      return;
    }

    const submittedQuestion = question.trim();
    const run = await submitAnalysis(
      [
        {
          name: "high_level",
          arguments: {},
        },
      ],
      true,
    );
    await saveMessage({
      role: "user",
      content: submittedQuestion,
      analysisRunId: run.id,
    });
    await saveMessage({
      role: "assistant",
      content:
        "Started a high-level overview for your question. Open the run to watch progress and view outputs.",
      analysisRunId: run.id,
    });
    setQuestion("");
    onSubmitted();
    router.push(`/workspaces/${workspaceId}/runs/${run.id}`);
  }

  return (
    <div className="sticky bottom-0 border-t border-slate-200 bg-white shadow-[0_-8px_20px_rgba(15,23,42,0.04)]">
      <div className="mx-auto max-w-5xl px-4 pt-3">
        {isLoadingMessages ? (
          <p className="pb-2 text-xs text-slate-500">Loading conversation...</p>
        ) : messages.length > 0 ? (
          <div className="mb-3 max-h-40 space-y-2 overflow-y-auto rounded-md border border-slate-200 bg-slate-50 p-3">
            {messages.map((message) => (
              <ChatMessage
                key={message.id}
                message={message}
                workspaceId={workspaceId}
              />
            ))}
          </div>
        ) : (
          <p className="mb-3 text-xs text-slate-500">
            Ask a question to start an analysis. You will be taken to the run
            detail page for progress and outputs.
          </p>
        )}
      </div>

      <form
        className="mx-auto flex max-w-5xl flex-col gap-3 px-4 pb-4 sm:flex-row"
        onSubmit={handleSubmit}
      >
        <textarea
          className="min-h-12 flex-1 resize-none rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-950 placeholder:text-slate-400"
          disabled={!datasetId || isSubmitting || atQuestionLimit}
          onChange={(event) => setQuestion(event.target.value)}
          placeholder={
            !datasetId
              ? "Upload a dataset before asking a question."
              : atQuestionLimit
                ? "Question limit reached for this conversation."
                : "Ask about this dataset..."
          }
          value={question}
        />
        <Button
          className="sm:self-stretch"
          disabled={
            !datasetId ||
            !workspaceId ||
            isSubmitting ||
            !question.trim() ||
            atQuestionLimit ||
            atJobLimit
          }
          type="submit"
        >
          {isSubmitting ? "Sending..." : "Send"}
        </Button>
      </form>

      <div className="mx-auto flex max-w-5xl flex-wrap items-center gap-x-4 gap-y-1 px-4 pb-4 text-xs text-slate-500">
        {usage ? (
          <p>
            Questions used: {usage.used}/{usage.limit}
            {atQuestionLimit ? " · limit reached" : ""}
          </p>
        ) : null}
        {atJobLimit ? (
          <p className="text-amber-700">
            Two analyses are already active. Wait for one to finish.
          </p>
        ) : null}
      </div>

      {error ? (
        <p className="mx-auto max-w-5xl px-4 pb-3 text-sm text-red-600">
          {error}
        </p>
      ) : null}
      {conversationError ? (
        <p className="mx-auto max-w-5xl px-4 pb-3 text-sm text-red-600">
          {conversationError}
        </p>
      ) : null}
    </div>
  );
}
