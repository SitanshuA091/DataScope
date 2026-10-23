"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { useConversation } from "@/hooks/use-conversation";
import { useRunResults } from "@/hooks/use-run-results";
import { formatDateTime } from "@/lib/formatters";
import type { Message } from "@/types/conversation";
import { ChartGallery } from "./chart-gallery";
import { ToolResponseViewer } from "./tool-response-viewer";

function parseAssistantContent(content: string) {
  const marker = "Key findings:";
  if (!content.includes(marker)) {
    return { mainText: content, findings: [] };
  }
  const parts = content.split(marker);
  const mainText = parts[0].trim();
  const rawFindings = parts.slice(1).join(marker).trim();
  const findings = rawFindings
    .split("\n")
    .map((line) => line.replace(/^[-*]\s*/, "").trim())
    .filter(Boolean);
  return { mainText, findings };
}

function MessageToolPreview({
  runId,
  workspaceId,
}: {
  runId: string;
  workspaceId?: string;
}) {
  const [expanded, setExpanded] = useState(false);
  const { results, isLoading, error } = useRunResults(
    runId,
    expanded ? "completed" : null,
  );
  const [activeTool, setActiveTool] = useState<string | null>(null);

  const metrics = results?.metrics ?? {};
  const toolNames = Object.keys(metrics).filter((key) => key !== "_agent");
  const currentTool =
    activeTool && toolNames.includes(activeTool) ? activeTool : toolNames[0];
  const toolData = currentTool
    ? (metrics[currentTool] as Record<string, unknown>)
    : null;
  const artifacts = results?.artifacts ?? [];

  return (
    <div className="mt-3 border-t border-slate-200/80 pt-2.5">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <button
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-blue-700 hover:text-blue-800 transition"
          onClick={() => setExpanded((prev) => !prev)}
          type="button"
        >
          <span>
            {expanded
              ? "▾ Hide computed tool output"
              : "▸ View computed tool output & charts"}
          </span>
          {results?.cache_hit ? (
            <span className="rounded bg-emerald-50 px-1.5 py-0.5 text-[10px] font-medium text-emerald-700 border border-emerald-200">
              ⚡ Cached
            </span>
          ) : null}
        </button>
        {workspaceId ? (
          <Link
            className="text-[11px] font-medium text-slate-500 hover:text-blue-700 hover:underline"
            href={`/workspaces/${workspaceId}/runs/${runId}`}
          >
            Full run details →
          </Link>
        ) : null}
      </div>

      {expanded ? (
        <div className="mt-3 space-y-3 rounded-md border border-slate-200 bg-white p-3 text-slate-900 shadow-xs">
          {isLoading ? (
            <div className="flex items-center gap-2 py-4 text-xs text-slate-500">
              <span className="h-3 w-3 animate-spin rounded-full border-2 border-blue-600 border-t-transparent" />
              Loading tool output...
            </div>
          ) : error ? (
            <p className="text-xs text-red-600">{error}</p>
          ) : (
            <>
              {toolNames.length > 1 ? (
                <div className="flex flex-wrap gap-1 border-b border-slate-100 pb-2">
                  {toolNames.map((name) => (
                    <button
                      className={`rounded px-2.5 py-1 text-xs font-medium capitalize transition ${
                        currentTool === name
                          ? "bg-blue-600 text-white"
                          : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                      }`}
                      key={name}
                      onClick={() => setActiveTool(name)}
                      type="button"
                    >
                      {name.replaceAll("_", " ")}
                    </button>
                  ))}
                </div>
              ) : null}

              {currentTool && toolData ? (
                <div className="max-h-96 overflow-y-auto">
                  <ToolResponseViewer data={toolData} toolName={currentTool} />
                </div>
              ) : null}

              {artifacts.length > 0 ? (
                <div className="pt-2">
                  <ChartGallery artifacts={artifacts} />
                </div>
              ) : null}
            </>
          )}
        </div>
      ) : null}
    </div>
  );
}

function ChatMessage({
  message,
  workspaceId,
}: {
  message: Message;
  workspaceId?: string;
}) {
  const isUser = message.role === "user";

  if (isUser) {
    return (
      <div className="flex justify-end">
        <div className="max-w-[85%] rounded-2xl rounded-tr-xs bg-blue-600 px-4 py-2.5 text-white shadow-xs sm:max-w-[75%]">
          <div className="flex items-baseline justify-between gap-3 text-[11px] text-blue-100">
            <span className="font-semibold uppercase tracking-wider">You</span>
            <span>{formatDateTime(message.created_at)}</span>
          </div>
          <p className="mt-1 whitespace-pre-wrap text-sm leading-relaxed">
            {message.content}
          </p>
        </div>
      </div>
    );
  }

  const { mainText, findings } = parseAssistantContent(message.content);

  return (
    <div className="flex justify-start">
      <div className="max-w-[92%] rounded-2xl rounded-tl-xs border border-slate-200 bg-white px-4 py-3 text-slate-900 shadow-xs sm:max-w-[85%]">
        <div className="flex items-baseline justify-between gap-3 text-[11px] text-slate-500">
          <span className="font-semibold uppercase tracking-wider text-blue-700 flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-blue-600 inline-block" />
            AI Analyst
          </span>
          <span>{formatDateTime(message.created_at)}</span>
        </div>

        <p className="mt-1.5 whitespace-pre-wrap text-sm leading-relaxed text-slate-800">
          {mainText}
        </p>

        {findings.length > 0 ? (
          <div className="mt-3 rounded-lg border border-blue-100 bg-blue-50/50 p-3">
            <p className="text-[11px] font-semibold uppercase tracking-wider text-blue-900">
              Key Findings
            </p>
            <ul className="mt-1.5 space-y-1 text-xs text-slate-800">
              {findings.map((item, idx) => (
                <li className="flex items-start gap-1.5" key={idx}>
                  <span className="mt-0.5 text-blue-600 font-bold">•</span>
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </div>
        ) : null}

        {message.analysis_run_id ? (
          <MessageToolPreview
            runId={message.analysis_run_id}
            workspaceId={workspaceId}
          />
        ) : null}
      </div>
    </div>
  );
}

const QUICK_PROMPTS = [
  "High-level overview & dataset shape",
  "Check data quality & missing values",
  "Analyze numeric column distributions",
  "Find correlations between variables",
];

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
  const [question, setQuestion] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const {
    messages,
    usage,
    isLoading: isLoadingMessages,
    isSending,
    error: conversationError,
    sendChat,
  } = useConversation(datasetId);

  const atQuestionLimit = usage?.remaining === 0;
  const atJobLimit = activeJobCount >= 2;

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isSending]);

  async function handleSend(queryToSend?: string) {
    const text = (queryToSend ?? question).trim();
    if (!text || !datasetId || isSending || atQuestionLimit || atJobLimit) {
      return;
    }

    setQuestion("");
    try {
      await sendChat(text);
      onSubmitted();
    } catch {}
  }

  function handleKeyDown(event: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      void handleSend();
    }
  }

  return (
    <div className="flex min-h-0 flex-1 flex-col bg-white">
      <div className="border-b border-slate-200 px-4 py-2">
        <div className="mx-auto flex max-w-4xl items-center gap-2 text-xs text-slate-500">
          <span className="relative flex h-2 w-2">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
            <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-500" />
          </span>
          <span className="font-semibold text-slate-800">Dataset AI Analyst</span>
          {usage ? (
            <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[11px] font-medium text-slate-600">
              {usage.used}/{usage.limit} questions
            </span>
          ) : null}
        </div>
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto bg-slate-50/70 px-4 py-4">
        <div className="mx-auto max-w-4xl space-y-3">
          {isLoadingMessages ? (
            <p className="py-2 text-xs text-slate-500">
              Loading conversation history...
            </p>
          ) : messages.length > 0 ? (
            <>
              {messages.map((message) => (
                <ChatMessage
                  key={message.id}
                  message={message}
                  workspaceId={workspaceId}
                />
              ))}
              {isSending ? (
                <div className="flex justify-start">
                  <div className="flex items-center gap-2 rounded-2xl rounded-tl-xs border border-blue-200 bg-blue-50/60 px-4 py-3 text-xs text-blue-900 shadow-xs">
                    <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-blue-600 border-t-transparent" />
                    <span>Analyzing dataset & running tools...</span>
                  </div>
                </div>
              ) : null}
              <div ref={messagesEndRef} />
            </>
          ) : (
            <div className="rounded-xl border border-dashed border-slate-200 bg-white p-6 text-center">
              <p className="text-xs font-medium text-slate-600">
                Ask any question about your dataset. The analyst will plan the
                right tools, reuse cached results, and return explanations
                directly in the chat.
              </p>
              <div className="mt-3 flex flex-wrap justify-center gap-1.5">
                {QUICK_PROMPTS.map((prompt) => (
                  <button
                    className="rounded-full border border-slate-200 bg-white px-3 py-1 text-xs text-slate-700 transition hover:border-blue-400 hover:bg-blue-50 hover:text-blue-800"
                    disabled={!datasetId || isSending}
                    key={prompt}
                    onClick={() => void handleSend(prompt)}
                    type="button"
                  >
                    {prompt}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="border-t border-slate-200 bg-white px-4 py-3">
        <div className="mx-auto max-w-4xl">
          <form
            className="flex flex-col gap-2 sm:flex-row sm:items-end"
            onSubmit={(event) => {
              event.preventDefault();
              void handleSend();
            }}
          >
            <textarea
              className="max-h-32 min-h-[50px] w-full flex-1 resize-none rounded-xl border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-950 placeholder:text-slate-400 focus:border-blue-500 focus:outline-hidden focus:ring-1 focus:ring-blue-500"
              disabled={!datasetId || isSending || atQuestionLimit}
              onChange={(event) => setQuestion(event.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={
                !datasetId
                  ? "Upload a dataset before asking a question."
                  : atQuestionLimit
                    ? "Question limit reached for this session."
                    : "Ask a question about this dataset (Enter to send, Shift+Enter for newline)..."
              }
              rows={2}
              value={question}
            />
            <Button
              className="h-11 shrink-0 rounded-xl sm:w-28"
              disabled={
                !datasetId ||
                isSending ||
                !question.trim() ||
                atQuestionLimit ||
                atJobLimit
              }
              type="submit"
            >
              {isSending ? (
                <span className="flex items-center gap-1.5">
                  <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-white border-t-transparent" />
                  Thinking
                </span>
              ) : (
                "Send"
              )}
            </Button>
          </form>

          {atJobLimit ? (
            <p className="mt-1 text-xs text-amber-700">
              Two analyses are already active. Wait for one to finish before
              starting a new run.
            </p>
          ) : null}

          {conversationError ? (
            <p className="mt-1 text-xs text-red-600">{conversationError}</p>
          ) : null}
        </div>
      </div>
    </div>
  );
}