import type { AnalysisInterpretation } from "@/types/analysis";

export function InterpretationPanel({
  explanation,
}: {
  explanation: AnalysisInterpretation | null | undefined;
}) {
  if (!explanation) {
    return null;
  }

  const answer =
    typeof explanation.answer === "string" ? explanation.answer : null;
  const findings = Array.isArray(explanation.key_findings)
    ? explanation.key_findings.filter(
        (item): item is string => typeof item === "string",
      )
    : [];
  const limitations = Array.isArray(explanation.limitations)
    ? explanation.limitations.filter(
        (item): item is string => typeof item === "string",
      )
    : [];
  const followUps = Array.isArray(explanation.follow_up_questions)
    ? explanation.follow_up_questions.filter(
        (item): item is string => typeof item === "string",
      )
    : [];

  if (!answer && findings.length === 0 && limitations.length === 0) {
    return null;
  }

  return (
    <section className="rounded-xl border border-blue-200 bg-gradient-to-br from-blue-50/80 to-slate-50 p-4">
      <div className="flex items-center gap-2 text-blue-800">
        <span aria-hidden className="text-sm">
          ✦
        </span>
        <h3 className="text-xs font-semibold uppercase tracking-wider">
          AI interpretation
        </h3>
      </div>
      <p className="mt-1 text-xs text-slate-500">
        Separate from computed tool output — grounded in structured results.
      </p>

      {answer ? (
        <p className="mt-3 text-sm leading-relaxed text-slate-950">{answer}</p>
      ) : null}

      {findings.length > 0 ? (
        <div className="mt-3 border-t border-blue-100 pt-3">
          <p className="text-xs font-semibold text-slate-800">Key findings</p>
          <ul className="mt-1.5 list-inside list-disc space-y-1 text-xs text-slate-700">
            {findings.map((finding) => (
              <li key={finding}>{finding}</li>
            ))}
          </ul>
        </div>
      ) : null}

      {limitations.length > 0 ? (
        <div className="mt-3 border-t border-blue-100 pt-3">
          <p className="text-xs font-semibold text-slate-800">Limitations</p>
          <ul className="mt-1.5 list-inside list-disc space-y-1 text-xs text-slate-600">
            {limitations.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>
      ) : null}

      {followUps.length > 0 ? (
        <div className="mt-3 flex flex-wrap gap-1.5 border-t border-blue-100 pt-3">
          <span className="text-xs font-medium text-slate-600">
            Follow-ups:
          </span>
          {followUps.map((question) => (
            <span
              className="rounded-full bg-white px-2.5 py-0.5 text-xs text-blue-700 shadow-xs"
              key={question}
            >
              {question}
            </span>
          ))}
        </div>
      ) : null}
    </section>
  );
}
