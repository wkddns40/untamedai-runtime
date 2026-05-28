# Untamed Companion Runtime

Public package skeleton for a LangGraph-based companion runtime.

This repository is intentionally separate from the private product repository.
It starts with no private git history and should only contain reusable runtime
code, examples, tests, and documentation approved for public release.

## Current Status

Core graph skeleton, provider interfaces, store interfaces, prompt providers,
SSE adapters, and FastAPI route factory are available.

## License

MIT.

## Intended Scope

- LangGraph chat graph runtime
- naming ceremony state machine
- SSE event adapter
- store/provider interfaces
- neutral prompt provider with app-owned override support
- in-memory demo and tests
- optional FastAPI, Supabase, and Postgres integrations

## Prompt Override

```python
from untamed_companion.graph import GraphRuntime
from untamed_companion.prompts import StaticPromptProvider

runtime = GraphRuntime(
    prompt_provider=StaticPromptProvider(chat_prompt="Your app-owned prompt.")
)
```

## Out of Scope

- product frontend
- private prompts and brand copy
- production deployment config
- billing/webhooks
- service role keys or project-specific environment values
