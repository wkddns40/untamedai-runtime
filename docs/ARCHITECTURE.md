# Architecture

`untamedai-runtime` is a small public runtime surface around LangGraph. It keeps
graph behavior, event contracts, storage, model providers, prompts, and web
transport separate so application teams can replace each part without copying
product-specific code.

## Main Modules

| Module | Role |
| --- | --- |
| `untamed_companion.graph` | Builds chat, greeting, and daily emotion graphs. |
| `untamed_companion.sse` | Converts graph events into public SSE frames. |
| `untamed_companion.store` | Defines async companion memory/profile storage. |
| `untamed_companion.providers` | Defines LLM, embedding, and weather providers. |
| `untamed_companion.prompts` | Builds neutral default prompts and overrides. |
| `untamed_companion.fastapi` | Provides an optional route factory. |

## Runtime Dependency Flow

```text
consumer app
  -> GraphRuntime
      -> provider implementations
      -> store implementation
      -> prompt provider
  -> build_chat_graph(...)
  -> forward_graph_sse(...)
  -> FastAPI StreamingResponse or custom transport
```

`GraphRuntime` is the dependency injection point. If a dependency is omitted,
the runtime falls back to deterministic fake providers where possible. This is
why the test suite runs without network access or secrets.

## Graphs

### Chat Graph

The chat graph normalizes session state, handles coffee turns, resolves naming
intents, retrieves memory/context, composes a prompt, generates a response, and
persists the turn when a store is configured.

Important event paths:

- regular chat: `stream -> end`
- companion naming: `name_reveal -> stream -> end`
- user intro: `user_name_set -> stream -> end`
- coffee turn: `coffee_request`

### Greeting Graph

The greeting graph emits one `greeting` event. It uses the configured
`GreetingResponder` and prompt provider.

### Emotion Graph

The emotion graph analyzes daily logs through the configured `EmotionAnalyzer`.
It skips empty log sets and otherwise returns an `analysis` mapping and
`new_summary`.

## Stores

The store interface is async and intentionally narrow. The graph only needs
profile reads/writes, recent chat logs, semantic chat search, and daily emotion
rows. Implementations can be in-memory, Supabase, Postgres-backed, or app-owned.

## Providers

The provider protocols are split by responsibility:

- `ChatResponder`
- `GreetingResponder`
- `EmotionAnalyzer`
- `EmbeddingProvider`
- `WeatherProvider`

`LLMProvider` combines chat, greeting, and emotion analysis for providers that
offer all three.

## Prompt Ownership

Default prompts are neutral and public-safe. Product copy, brand voice, and
private persona instructions should be supplied by the consumer app through a
custom `PromptProvider`.

## Transport

The package does not require FastAPI. `untamed_companion.sse` can forward any
compiled graph as SSE frames. The FastAPI route factory is an optional adapter
for common web apps.
