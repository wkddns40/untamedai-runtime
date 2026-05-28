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

from untamed_companion.fastapi import create_chat_router
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

## Metrics Hook

Pass `metric_hook` to observe stream route, bucket, status, duration, and event
counts:

```python
from untamed_companion.sse import StreamMetrics


def metric_hook(metric: StreamMetrics) -> None:
    print(metric.route, metric.status, metric.event_counts)
```

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
