# Integrations

This package is designed to be embedded inside a consumer-owned service. The
consumer app owns authentication, authorization, persistence deployment,
observability, and prompt policy.

## FastAPI

Install:

```bash
pip install "untamedai-runtime[fastapi]"
```

Create a router:

```python
from fastapi import FastAPI, HTTPException, Request

from untamed_companion.fastapi import ChatRouterSettings, create_chat_router
from untamed_companion.graph import GraphRuntime
from untamed_companion.store import InMemoryCompanionStore

app = FastAPI()
runtime = GraphRuntime(companion_store=InMemoryCompanionStore())


async def auth_hook(request: Request, companion_id: str) -> None:
    if not request.headers.get("authorization"):
        raise HTTPException(status_code=401, detail="missing token")


app.include_router(
    create_chat_router(
        runtime=runtime,
        prefix="/api",
        auth_hook=auth_hook,
        settings=ChatRouterSettings(history_limit_default=20, history_limit_max=50),
    )
)
```

Routes:

- `GET /api/chat/{companion_id}/history`
- `GET /api/chat/{companion_id}/greeting`
- `POST /api/chat/{companion_id}/stream`

`POST /stream` body:

```json
{
  "message": "hello",
  "user_name": "Min",
  "lang": "en",
  "type": "chat",
  "companion": {"name": "Luna"}
}
```

Stable route factory extension points:

- `runtime`: graph runtime dependencies.
- `prefix`: router path prefix.
- `auth_hook`: sync or async authorization callback.
- `metric_hook`: stream metrics callback.
- `config_factory`: LangGraph config builder for thread/checkpointer IDs.
- `bucket_resolver`: request-to-metrics bucket callback.
- `settings`: `ChatRouterSettings` for history limits and SSE headers.

`auth_hook` receives the raw `Request` and `companion_id`:

```python
async def auth_hook(request: Request, companion_id: str) -> None:
    token = request.headers.get("authorization")
    if token != "Bearer demo-token":
        raise HTTPException(status_code=401, detail="missing or invalid token")
    if not await owns_companion(token, companion_id):
        raise HTTPException(status_code=403, detail="companion access denied")
```

Use `config_factory` when your checkpointer or graph config needs an
application-owned thread ID:

```python
def config_factory(thread_id: str) -> dict[str, object]:
    return {"configurable": {"thread_id": f"tenant-a:{thread_id}"}}
```

Use `bucket_resolver` when metrics should group requests by canary, tenant, or
transport:

```python
def bucket_resolver(request: Request) -> str:
    return request.headers.get("x-runtime-bucket", "stable")
```

## Metrics Hook

Pass `metric_hook` to observe stream route, bucket, status, duration, and event
counts:

```python
from untamed_companion.sse import StreamMetrics


def metric_hook(metric: StreamMetrics) -> None:
    print(metric.route, metric.status, metric.event_counts)
```

## Non-FastAPI Transport

If your service does not use FastAPI, use the SSE adapter directly and adapt the
async iterator to your web framework:

```python
from untamed_companion.graph import GraphRuntime, build_chat_graph
from untamed_companion.sse import forward_graph_sse

runtime = GraphRuntime()
graph = build_chat_graph(runtime=runtime)

frames = forward_graph_sse(
    graph,
    {
        "companion_id": "demo",
        "last_user_message": "hello",
        "user_lang": "en",
    },
    config={"configurable": {"thread_id": "demo"}},
    route="/chat/stream",
)
```

Each item yielded by `frames` is one serialized SSE frame.

## Store Implementations

Use `InMemoryCompanionStore` for tests and demos:

```python
from untamed_companion.graph import GraphRuntime
from untamed_companion.store import InMemoryCompanionStore

runtime = GraphRuntime(companion_store=InMemoryCompanionStore())
```

For production, implement `CompanionStore` or use the optional Supabase adapter:

```python
from untamed_companion.store import SupabaseCompanionStore

store = SupabaseCompanionStore(
    url="https://your-project.supabase.co",
    key="your-key",
)
```

Required store methods:

- `get_companion`
- `put_companion`
- `add_chat_log`
- `get_recent_chat`
- `search_chat`
- `get_emotions`
- `put_emotion`

## Provider Implementations

For tests, use fake providers:

```python
from untamed_companion.providers import FakeEmbeddingProvider, FakeLLMProvider

runtime = GraphRuntime(
    llm_provider=FakeLLMProvider(),
    embedding_provider=FakeEmbeddingProvider(dimensions=8),
)
```

For OpenAI:

```bash
pip install "untamedai-runtime[openai]"
```

```python
from untamed_companion.providers import OpenAIProvider

runtime = GraphRuntime(llm_provider=OpenAIProvider(api_key="..."))
```

Provider protocols:

- `ChatResponder.generate_chat_response(state)`
- `GreetingResponder.generate_greeting(state)`
- `EmotionAnalyzer.analyze_emotion(state)`
- `EmbeddingProvider.embed_text(text)`
- `WeatherProvider.get_weather(location=..., lang=...)`

## Prompt Providers

Use the default neutral prompts for demos and tests. Supply a custom prompt
provider for application-specific tone:

```python
from untamed_companion.prompts import StaticPromptProvider

runtime = GraphRuntime(
    prompt_provider=StaticPromptProvider(
        chat_prompt="Your app-owned prompt.",
    )
)
```

For larger apps, implement `PromptProvider` with `build_chat_prompt`,
`build_greeting_prompt`, and `build_emotion_prompt`.
