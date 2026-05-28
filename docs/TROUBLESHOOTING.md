# Troubleshooting

## Import Fails For Optional Integrations

Install the matching extra:

```bash
pip install "untamedai-runtime[fastapi]"
pip install "untamedai-runtime[openai]"
pip install "untamedai-runtime[supabase]"
pip install "untamedai-runtime[postgres]"
```

The core package intentionally does not install FastAPI, OpenAI, Supabase, or
Postgres dependencies.

## FastAPI Routes Return 401 Or 403

Authentication is application-owned. Check the `auth_hook` passed to
`create_chat_router(...)`. The package does not create sessions, API keys, or
tenant ownership checks.

## Stream Opens But No Assistant Message Appears

Inspect the SSE frames first. A valid frame looks like:

```text
data: {"type": "stream", "content": "Hello"}
```

If only `end` appears, verify that the graph produced a `stream`, `greeting`,
or shortcut event. If an `error` frame appears, check application logs around
provider, store, or checkpointer calls.

## Event Inspector Shows End Without Content

This is expected in the demo UI. `end` is a completion marker, so the inspector
shows completion state and `intent` instead of rendering its `content` as chat
text.

## Postgres Extra Changes LangGraph Versions

Use `untamedai-runtime>=0.3.1`. The `postgres` extra uses
`langgraph-checkpoint-postgres>=3,<4`, which resolves with current LangGraph
1.x checkpoint packages.

## Supabase Store Cannot Find Tables Or RPC

The application owns schema names. Either use the adapter defaults documented
in [Persistence](PERSISTENCE.md), or pass custom table, column, and RPC names
to `SupabaseCompanionStore`.

## Demo State Does Not Persist

The showcase uses `InMemoryCompanionStore`. Restarting the process clears
state. Use an application-owned `CompanionStore` implementation or the optional
Supabase adapter for persistence.

## Prompt Output Does Not Match The Consumer App

The package default prompts are neutral and public-safe. Use
`StaticPromptProvider` or implement `PromptProvider` in the consumer app for
brand, policy, and tone.
