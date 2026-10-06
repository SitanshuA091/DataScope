"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { useAnalysisRun } from "@/hooks/use-analysis-run";

export function ChatPanel({
  datasetId,
  onSubmitted,
}: {
  datasetId: string | null;
  onSubmitted: () => void;
}) {
  const [question, setQuestion] = useState("");
  const { submitAnalysis, isSubmitting, error } = useAnalysisRun(datasetId);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!question.trim() || !datasetId) {
      return;
    }

    await submitAnalysis(
      [
        {
          name: "high_level_summary",
          arguments: { question: question.trim() },
        },
      ],
      true,
    );
    setQuestion("");
    onSubmitted();
  }

  return (
    <div className="sticky bottom-0 border-t border-slate-200 bg-white p-4 shadow-[0_-8px_20px_rgba(15,23,42,0.04)]">
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
          disabled={!datasetId || isSubmitting || !question.trim()}
          type="submit"
        >
          {isSubmitting ? "Sending..." : "Send"}
        </Button>
      </form>
      {error ? (
        <p className="mx-auto mt-2 max-w-5xl text-sm text-red-600">{error}</p>
      ) : null}
    </div>
  );
}
