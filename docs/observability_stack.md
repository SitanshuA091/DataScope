- **App-level traces, metrics and logs: use OpenTelemetry with Grafana.**
  - OpenTelemetry is already in your dependency list, so you're only missing the wiring.
  - The Grafana stack is Tempo for traces, Loki for logs and Prometheus for metrics.
  - **Locally:** the single `grafana/otel-lgtm` Docker image runs all of it, with Grafana at localhost:3000. Move your frontend off that port.
  - **Deployed:** use Grafana Cloud's free tier, since self-hosting Grafana on Render would cost money. Check its current limits and retention.
  - **Alternatives:** SigNoz (heavier to self-host) or Jaeger (traces only). Sentry's free tier is worth adding for error alerts.
  - **Useful spans:** API request, Celery task, planner call, each tool, interpreter call and R2 calls. Tag them with `run_id` so a trace lines up with `analysis_runs` in Postgres.
- **Agent-level traces and LLM-as-judge: LangSmith works without LangChain.**
  - It can trace plain Python functions and can take LiteLLM callbacks, so it fits your hand-written orchestrator.
  - Its free developer tier has a monthly trace cap, so check the current limit.
  - **Open-source alternatives:** Langfuse (self-host or free cloud, with good LiteLLM support), Arize Phoenix and Opik. If open source or self-hosting matters to you, Langfuse is the closest match.
  - Pick one agent-tracing tool, not several.
- **Judging the chat tool:**
  - **Method:** build a small dataset of CSVs with expected tool routing, run the chat flow offline and score outputs with a judge. Compare prompt versions before and after each change.
  - **Criteria worth scoring:**
    - **Tool routing:** did the planner pick the right tool and valid arguments?
    - **Grounding:** does every number in the answer appear in the tool output?
    - **Invented statistics:** flag any number or claim not in the tool output.
    - **Clarification:** does it ask when it should, and not otherwise?
    - **Clarity:** is the answer concise and useful?
  - **Judge model:** use a different model than the one being judged. If the interpreter is Gemini, judge with a Groq model, for example.
  - **Checks that need no judge:** routing correctness and numeric grounding can be checked with plain code. Use the judge only for tone and clarity.
  - **Online scoring:** later, score a small sample of real traces as well.
- **Privacy:** traces sent to these tools will contain prompts and tool outputs. Your design already sends aggregates only, so keep that, and don't trace the 20-row samples unmasked.
- **Suggested order for V1:**
  1. Add correlation IDs and the missing logging pieces.
  2. Run OpenTelemetry with local `otel-lgtm`.
  3. Add LangSmith or Langfuse for the planner and interpreter.
  4. Build the evaluation set and judge.
  5. Move to Grafana Cloud when you deploy.
- **Postgres already holds your own audit trail** (plans, tool arguments, results, errors). Traces are for debugging and latency, not a replacement for that.