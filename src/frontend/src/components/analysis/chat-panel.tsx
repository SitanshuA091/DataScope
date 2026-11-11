"use client";

import Link from "next/link";
import { useEffect, useRef, useState, type ReactNode } from "react";
import { AppLogo } from "@/components/ui/app-logo";
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

function Svg({
  className = "h-4 w-4",
  children,
}: {
  className?: string;
  children: ReactNode;
}) {
  return (
    <svg
      className={className}
      fill="none"
      stroke="currentColor"
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeWidth="2"
      viewBox="0 0 24 24"
    >
      {children}
    </svg>
  );
}

function AgentAvatar({
  large = false,
  pulsing = false,
}: {
  large?: boolean;
  pulsing?: boolean;
}) {
  return (
    <div
      className={`grid shrink-0 place-items-center rounded-xl bg-white/80 ring-1 ring-slate-200 shadow-xs ${
        large ? "h-14 w-14" : "h-8 w-8"
      } ${pulsing ? "animate-pulse" : ""}`}
    >
      <AppLogo className={large ? "h-8 w-8" : "h-5 w-5"} />
    </div>
  );
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
    <div className="mt-3 overflow-hidden rounded-xl border border-slate-200 bg-white/70 shadow-xs backdrop-blur">
      <div className="flex flex-wrap items-center justify-between gap-2 px-3 py-2.5">
        <button
          className="flex items-center gap-2.5 text-xs font-medium text-slate-700 transition hover:text-slate-950"
          onClick={() => setExpanded((prev) => !prev)}
          type="button"
        >
          <span className="grid h-6 w-6 place-items-center rounded-full bg-emerald-100 text-emerald-700">
            <Svg className="h-3.5 w-3.5">
              <path d="M20 6 9 17l-5-5" />
            </Svg>
          </span>
          <span>{expanded ? "Hide tool output" : "Tool output & charts"}</span>
          <Svg
            className={`h-4 w-4 text-slate-400 transition-transform duration-200 ${
              expanded ? "rotate-180" : ""
            }`}
          >
            <path d="m6 9 6 6 6-6" />
          </Svg>
          {results?.cache_hit ? (
            <span className="rounded-full border border-emerald-200 bg-emerald-50 px-2 py-0.5 text-[10px] font-medium text-emerald-700">
              Cached
            </span>
          ) : null}
        </button>
        {workspaceId ? (
          <Link
            className="inline-flex items-center gap-1 text-[11px] font-medium text-slate-500 transition hover:text-blue-700"
            href={`/workspaces/${workspaceId}/runs/${runId}`}
          >
            Run details
            <Svg className="h-3 w-3">
              <path d="M5 12h14M13 6l6 6-6 6" />
            </Svg>
          </Link>
        ) : null}
      </div>

      {expanded ? (
        <div className="fade-up space-y-3 border-t border-slate-200 p-3 text-slate-900">
          {isLoading ? (
            <div className="flex items-center gap-2 py-3 text-xs text-slate-500">
              <span className="h-3 w-3 animate-spin rounded-full border-2 border-blue-600 border-t-transparent" />
              Loading tool output...
            </div>
          ) : error ? (
            <p className="text-xs text-red-600">{error}</p>
          ) : (
            <>
              {toolNames.length > 1 ? (
                <div className="inline-flex flex-wrap gap-1 rounded-lg bg-slate-100 p-1">
                  {toolNames.map((name) => (
                    <button
                      className={`rounded-md px-3 py-1 text-xs font-medium capitalize transition ${
                        currentTool === name
                          ? "bg-white text-slate-950 shadow-xs"
                          : "text-slate-600 hover:text-slate-900"
                      }`}
                      key={name}
                      onClick={() => setActiveTool(name)}
                      type="button"
                    >
                      {name.replaceAll("_", " ")}
                    </button>
                  ))}
                </div>
              ) : currentTool ? (
                <p className="text-xs font-medium capitalize text-slate-500">
                  {currentTool.replaceAll("_", " ")}
                </p>
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
      <div className="fade-up flex flex-col items-end">
        <div className="max-w-[85%] rounded-2xl rounded-br-md bg-blue-600 px-4 py-2.5 text-white shadow-sm">
          <p className="whitespace-pre-wrap text-sm leading-relaxed">
            {message.content}
          </p>
        </div>
        <span className="mt-1 text-[11px] text-slate-500">
          {formatDateTime(message.created_at)}
        </span>
      </div>
    );
  }

  const { mainText, findings } = parseAssistantContent(message.content);

  return (
    <div className="fade-up flex gap-3">
      <AgentAvatar />
      <div className="min-w-0 flex-1">
        <div className="flex items-baseline gap-2 text-xs text-slate-500">
          <span className="font-semibold text-slate-900">DataScope</span>
          <span>{formatDateTime(message.created_at)}</span>
        </div>

        <div className="mt-1.5 rounded-2xl rounded-tl-md border border-slate-200 bg-white/80 px-4 py-3 shadow-xs backdrop-blur">
          <p className="whitespace-pre-wrap text-sm leading-relaxed text-slate-800">
            {mainText}
          </p>

          {findings.length > 0 ? (
            <div className="mt-3 rounded-xl border border-blue-100 bg-blue-50/70 p-3">
              <p className="text-[11px] font-semibold uppercase tracking-wider text-blue-800">
                Key findings
              </p>
              <ul className="mt-2 space-y-1.5 text-sm text-slate-800">
                {findings.map((item, idx) => (
                  <li className="flex items-start gap-2" key={idx}>
                    <span className="mt-0.5 grid h-4 w-4 shrink-0 place-items-center rounded-full bg-blue-600 text-white">
                      <Svg className="h-2.5 w-2.5">
                        <path d="M20 6 9 17l-5-5" />
                      </Svg>
                    </span>
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
        </div>

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
  {
    label: "Dataset overview",
    hint: "Shape, types and summary",
    text: "High-level overview & dataset shape",
    icon: (
      <>
        <rect height="7" rx="1" width="7" x="3" y="3" />
        <rect height="7" rx="1" width="7" x="14" y="3" />
        <rect height="7" rx="1" width="7" x="3" y="14" />
        <rect height="7" rx="1" width="7" x="14" y="14" />
      </>
    ),
  },
  {
    label: "Data quality",
    hint: "Missing values and issues",
    text: "Check data quality & missing values",
    icon: (
      <>
        <path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z" />
        <path d="m9 12 2 2 4-4" />
      </>
    ),
  },
  {
    label: "Distributions",
    hint: "Numeric column spread",
    text: "Analyze numeric column distributions",
    icon: (
      <>
        <path d="M3 3v18h18" />
        <path d="M7 15v3M12 9v9M17 12v6" />
      </>
    ),
  },
  {
    label: "Correlations",
    hint: "Relationships between variables",
    text: "Find correlations between variables",
    icon: (
      <>
        <circle cx="7" cy="17" r="2" />
        <circle cx="17" cy="7" r="2" />
        <path d="M9 15l6-6" />
      </>
    ),
  },
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
  const usagePercent = usage
    ? Math.min(100, (usage.used / Math.max(usage.limit, 1)) * 100)
    : 0;

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
    <div className="flex min-h-0 flex-1 flex-col bg-transparent">
      <div className="min-h-0 flex-1 overflow-y-auto px-4 py-6">
        <div className="mx-auto max-w-3xl space-y-6">
          {isLoadingMessages ? (
            <div className="space-y-4">
              <div className="h-16 w-2/3 animate-pulse rounded-2xl bg-slate-200" />
              <div className="ml-auto h-10 w-1/2 animate-pulse rounded-2xl bg-slate-200" />
            </div>
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
                <div className="fade-up flex gap-3">
                  <AgentAvatar pulsing />
                  <div className="min-w-0 flex-1">
                    <span className="text-xs font-semibold text-slate-900">
                      DataScope
                    </span>
                    <div className="mt-1.5 inline-flex items-center gap-3 rounded-2xl rounded-tl-md border border-slate-200 bg-white/80 px-4 py-3 shadow-xs backdrop-blur">
                      <span className="flex items-center gap-1">
                        {[0, 150, 300].map((delay) => (
                          <span
                            className="h-1.5 w-1.5 animate-bounce rounded-full bg-blue-600"
                            key={delay}
                            style={{ animationDelay: `${delay}ms` }}
                          />
                        ))}
                      </span>
                      <span className="text-sm text-slate-600">
                        Planning and running tools...
                      </span>
                    </div>
                  </div>
                </div>
              ) : null}
              <div ref={messagesEndRef} />
            </>
          ) : (
            <div className="fade-up flex flex-col items-center pt-8 text-center">
              <AgentAvatar large />
              <h2 className="mt-4 text-xl font-semibold text-slate-900">
                What would you like to investigate?
              </h2>
              <p className="mt-1.5 max-w-md text-sm text-slate-500">
                The agent plans the right tools, reuses cached results, and
                explains the computed output.
              </p>
              <div className="mt-6 grid w-full max-w-xl gap-3 sm:grid-cols-2">
                {QUICK_PROMPTS.map((prompt) => (
                  <button
                    className="card-lift flex items-start gap-3 rounded-xl border border-slate-200 bg-white/80 p-3.5 text-left shadow-xs disabled:opacity-50"
                    disabled={!datasetId || isSending || atJobLimit}
                    key={prompt.label}
                    onClick={() => void handleSend(prompt.text)}
                    type="button"
                  >
                    <span className="grid h-9 w-9 shrink-0 place-items-center rounded-lg bg-blue-50 text-blue-700 ring-1 ring-blue-100">
                      <Svg className="h-5 w-5">{prompt.icon}</Svg>
                    </span>
                    <span className="min-w-0">
                      <span className="block text-sm font-semibold text-slate-900">
                        {prompt.label}
                      </span>
                      <span className="mt-0.5 block text-xs text-slate-500">
                        {prompt.hint}
                      </span>
                    </span>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="border-t border-slate-200 bg-white/60 px-4 py-4 backdrop-blur">
        <div className="mx-auto max-w-3xl">
          <div className="rounded-2xl border border-slate-300 bg-white/80 shadow-lg shadow-slate-900/5 transition focus-within:border-blue-500 focus-within:ring-2 focus-within:ring-blue-500/30">
            <form
              onSubmit={(event) => {
                event.preventDefault();
                void handleSend();
              }}
            >
              <textarea
                className="max-h-40 min-h-[56px] w-full resize-none bg-transparent px-4 pt-3.5 text-sm text-slate-950 placeholder:text-slate-400 focus:outline-hidden"
                disabled={!datasetId || isSending || atQuestionLimit}
                onChange={(event) => setQuestion(event.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={
                  !datasetId
                    ? "Upload a dataset before asking a question."
                    : atQuestionLimit
                      ? "Question limit reached for this session."
                      : "Ask DataScope to investigate this dataset..."
                }
                rows={2}
                value={question}
              />
              <div className="flex items-center justify-between gap-3 px-3 pb-3 pt-1">
                <div className="flex min-w-0 items-center gap-3">
                  <div className="flex items-center gap-1.5">
                    <AppLogo className="h-4 w-4" />
                    <span className="text-xs font-semibold text-slate-900">
                      DataScope
                    </span>
                  </div>
                  {usage ? (
                    <div
                      className="flex items-center gap-2"
                      title={`${usage.used} of ${usage.limit} questions used`}
                    >
                      <div className="h-1.5 w-16 overflow-hidden rounded-full bg-slate-200">
                        <div
                          className={`h-full rounded-full transition-all ${
                            atQuestionLimit ? "bg-red-600" : "bg-blue-600"
                          }`}
                          style={{ width: `${usagePercent}%` }}
                        />
                      </div>
                      <span className="text-[11px] font-medium text-slate-500">
                        {usage.used}/{usage.limit}
                      </span>
                    </div>
                  ) : null}
                  <span className="hidden text-[11px] text-slate-400 sm:inline">
                    Enter to send · Shift+Enter for new line
                  </span>
                </div>
                <button
                  aria-label="Send"
                  className="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-blue-600 text-white shadow-sm transition hover:bg-blue-500 active:scale-95 disabled:cursor-not-allowed disabled:bg-blue-600/40"
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
                    <span className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                  ) : (
                    <Svg className="h-4 w-4">
                      <path d="M12 19V5M5 12l7-7 7 7" />
                    </Svg>
                  )}
                </button>
              </div>
            </form>
          </div>

          {atJobLimit ? (
            <p className="mt-2 text-xs text-amber-700">
              Two analyses are already active. Wait for one to finish before
              starting a new run.
            </p>
          ) : null}

          {conversationError ? (
            <p className="mt-2 text-xs text-red-600">{conversationError}</p>
          ) : null}
        </div>
      </div>
    </div>
  );
}