```
                    ┌──────────────────┐
                    │   React / Next.js│
                    │      Frontend    │
                    └────────┬─────────┘
                             │ HTTPS
                             ▼
                    ┌──────────────────┐
                    │     FastAPI      │
                    │   API Backend    │
                    └───────┬──────────┘
                            │
             ┌──────────────┼──────────────┐
             ▼              ▼              ▼
        PostgreSQL       Redis/Queue    WebSocket
             │              │              │
             │              ▼              │
             │        Background Worker    │
             │              │              │
             │              ▼              │
             │         EDA Tools           │
             │              │              │
             │              ▼              │
             │          LLM API            │
             │                             │
             └──────────────┬──────────────┘
                            ▼
                     Results / Artifacts
```