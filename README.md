# Untamed Companion Runtime

LangGraph-based runtime primitives for emotionally adaptive AI companions.

This package exposes reusable graph builders, SSE event adapters, provider
interfaces, store interfaces, prompt overrides, FastAPI routes, deterministic
tests, and a local demo showcase. It is product-agnostic by design: application
copy, private prompts, production deployment config, billing, and secrets stay
outside this repository.

## Release Status

This package is an alpha runtime. Public APIs, event payload details, and
provider/store extension points may evolve before `1.0.0`, but published
patch/minor releases should remain backward compatible. Pin exact versions for
application use and follow the release policy before upgrading.

The FastAPI router is intentionally unauthenticated by default. Production
applications must pass `auth_hook` to `create_chat_router(...)` and enforce
their own ownership, session, API key, or tenant policy.

## Install

From source:

```bash
git clone https://github.com/wkddns40/untamedai-runtime.git
cd untamedai-runtime
pip install -e ".[fastapi,dev]"
```

From PyPI:

```bash
pip install untamedai-runtime
```

Optional extras:

```bash
pip install "untamedai-runtime[fastapi]"
pip install "untamedai-runtime[openai]"
pip install "untamedai-runtime[supabase]"
pip install "untamedai-runtime[postgres]"
```

Verify:

```bash
python -m pytest
```

## Quickstart

```python
from untamed_companion.graph import GraphRuntime, build_chat_graph
from untamed_companion.providers import FakeLLMProvider

runtime = GraphRuntime(llm_provider=FakeLLMProvider())
graph = build_chat_graph(runtime=runtime)

result = await graph.ainvoke(
    {
        "companion_id": "demo",
        "last_user_message": "your name is Luna",
        "user_lang": "en",
        "companion": {"name": "???"},
    }
)

print(result["emit"])
```

## FastAPI

```python
from fastapi import FastAPI

from untamed_companion.fastapi import ChatRouterSettings, create_chat_router
from untamed_companion.graph import GraphRuntime
from untamed_companion.store import InMemoryCompanionStore

app = FastAPI()
runtime = GraphRuntime(companion_store=InMemoryCompanionStore())
app.include_router(
    create_chat_router(
        runtime=runtime,
        prefix="/api",
        settings=ChatRouterSettings(history_limit_default=20, history_limit_max=50),
    )
)
```

Routes:

- `GET /api/chat/{companion_id}/history`
- `GET /api/chat/{companion_id}/greeting`
- `POST /api/chat/{companion_id}/stream`

Auth is app-owned. Pass `auth_hook` to `create_chat_router(...)` to enforce
ownership, sessions, API keys, or any other policy.

## Demo Showcase

```bash
pip install -e ".[fastapi,dev]"
python examples/demo_showcase/backend/app.py
```

Open:

```text
http://127.0.0.1:8000/demo
```

The showcase uses the public FastAPI router, in-memory store, fake providers,
SSE event inspector, Korean/English language toggle, reset endpoint, and daily
emotion dry-run.

## Prompt Override

```python
from untamed_companion.graph import GraphRuntime
from untamed_companion.prompts import StaticPromptProvider

runtime = GraphRuntime(
    prompt_provider=StaticPromptProvider(chat_prompt="Your app-owned prompt.")
)
```

## Event Contract

SSE frames are emitted as JSON in `data:` lines:

```text
data: {"type": "stream", "content": "Hello"}
```

Stable event types:

| Type | Purpose |
| --- | --- |
| `stream` | Assistant text chunk or complete deterministic message. |
| `end` | Stream completion marker. May include final `content` and `intent`. |
| `greeting` | First greeting response. |
| `name_reveal` | Companion name accepted. |
| `user_name_set` | User display name accepted. |
| `naming_prompt` | Runtime asks user to name the companion. |
| `coffee_request` | Coffee-turn shortcut event. |
| `error` | Stream failure frame. |

Golden fixtures live under `tests/golden/fixtures`. They compare public event
order and payloads with whitespace-tolerant diffs, using only fake providers
and in-memory state.

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Event Contract](docs/EVENT_CONTRACT.md)
- [Integrations](docs/INTEGRATIONS.md)
- [Migration Guide](docs/MIGRATION.md)
- [Public Release Audit](docs/PUBLIC_RELEASE_AUDIT.md)
- [Release Policy](docs/RELEASE_POLICY.md)
- [Roadmap](docs/ROADMAP.md)

## Intended Scope

- LangGraph chat, greeting, and daily emotion graph builders
- naming ceremony state machine
- SSE event adapter
- store/provider interfaces
- neutral prompt provider with app-owned override support
- in-memory demo and tests
- optional FastAPI, OpenAI, Supabase, and Postgres integrations

## Out of Scope

- product frontend
- private prompts and brand copy
- production deployment config
- billing/webhooks
- service role keys or project-specific environment values

## License

MIT.
