# API Stability

`untamedai-runtime` declares the following public compatibility surface stable
as of `1.0.0`.

## Stable Modules

- `untamed_companion.graph`
- `untamed_companion.sse`
- `untamed_companion.store`
- `untamed_companion.providers`
- `untamed_companion.prompts`
- `untamed_companion.fastapi`
- `untamed_companion.checkpoint`

## Stable Event Contract

The SSE frame format and event types documented in
[Event Contract](EVENT_CONTRACT.md) are stable.

Stable event types:

- `stream`
- `end`
- `greeting`
- `name_reveal`
- `user_name_set`
- `naming_prompt`
- `coffee_request`
- `error`

Consumers should switch on `type`, tolerate unknown fields, and avoid rendering
`end.content` as a second assistant message unless intentionally showing raw
protocol details.

## Stable Graph API

Stable graph builders:

- `build_chat_graph`
- `build_greeting_graph`
- `build_emotion_graph`
- `GraphRuntime`

The graph state `TypedDict` shapes are public integration contracts for provider
and store implementations. New optional fields may be added in minor releases.
Required field removals or behavior changes require a major version.

## Stable Store API

Stable store types:

- `CompanionStore`
- `CompanionRecord`
- `ChatLog`
- `EmotionLog`
- `InMemoryCompanionStore`
- `SupabaseCompanionStore`

Consumer-owned stores should implement the async `CompanionStore` protocol.
Adding optional fields to records is backward compatible. Removing protocol
methods or changing method meanings requires a major version.

## Stable Provider API

Stable provider protocols:

- `ChatResponder`
- `GreetingResponder`
- `EmotionAnalyzer`
- `LLMProvider`
- `EmbeddingProvider`
- `WeatherProvider`

Stable built-in providers:

- `FakeLLMProvider`
- `FakeEmbeddingProvider`
- `FakeWeatherProvider`
- `StaticWeatherProvider`
- `OpenAIProvider`

Provider implementations should treat state mappings as append-only. New
optional state keys may appear in minor releases.

## Stable Prompt API

Stable prompt provider types:

- `PromptProvider`
- `DefaultPromptProvider`
- `StaticPromptProvider`

Prompt text is intentionally consumer-owned. Default prompt wording may receive
backward-compatible clarifications, but prompt provider method names and
purposes are stable.

## Stable FastAPI API

Stable FastAPI route factory types:

- `create_chat_router`
- `ChatRouterSettings`
- `ChatRequest`
- `AuthHook`
- `ConfigFactory`
- `BucketResolver`

Stable routes created by the factory:

- `GET /chat/{companion_id}/history`
- `GET /chat/{companion_id}/greeting`
- `POST /chat/{companion_id}/stream`

The router remains unauthenticated by default. Production applications own
authentication and authorization through `auth_hook`.

Stream metrics use `untamed_companion.sse.MetricHook` and `StreamMetrics`.

## Stable Optional Extras

Stable extras:

- `fastapi`
- `openai`
- `supabase`
- `postgres`
- `dev`

Optional dependency version ranges may be widened in minor releases when the
public behavior remains compatible.

## Compatibility Rules

- Patch releases are backward compatible.
- Minor releases may add optional APIs and optional event fields.
- Public removals, renamed event types, or changed route semantics require a
  future major version.
- Security fixes may restrict unsafe behavior, with migration notes where
  practical.
