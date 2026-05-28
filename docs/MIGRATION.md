# Migration Guide

Use this guide when moving an existing companion app onto
`untamedai-runtime`.

## 1. Start With Fake Dependencies

First wire the graph with fake providers and an in-memory store. This confirms
that event ordering, routing, and basic UI rendering work without network
access or secrets.

```python
from untamed_companion.graph import GraphRuntime, build_chat_graph
from untamed_companion.providers import FakeEmbeddingProvider, FakeLLMProvider
from untamed_companion.store import InMemoryCompanionStore

runtime = GraphRuntime(
    llm_provider=FakeLLMProvider(),
    embedding_provider=FakeEmbeddingProvider(),
    companion_store=InMemoryCompanionStore(),
)
graph = build_chat_graph(runtime=runtime)
```

## 2. Attach Transport

If your service uses FastAPI, attach the route factory:

```python
app.include_router(create_chat_router(runtime=runtime, prefix="/api"))
```

If not, use `forward_graph_sse(...)` directly and adapt the returned async
iterator to your web framework.

## 3. Match Event Rendering

Render these user-visible events:

- `stream`
- `greeting`
- `coffee_request`, if your UI displays action events

Use these events for state updates:

- `name_reveal`
- `user_name_set`
- `end`
- `error`

Do not render `end.content` as a second assistant message unless your UI is a
raw protocol inspector.

## 4. Move Prompts Behind a Provider

Keep application prompts in your app. Implement `PromptProvider` or use
`StaticPromptProvider` while migrating.

## 5. Replace Fake Providers

Add model, embedding, and weather providers one at a time. Keep the golden
event tests passing after each replacement.

## 6. Replace Storage

Implement `CompanionStore` for your persistence layer. The runtime expects
these logical records:

- companion profile
- chat logs
- semantic chat search results
- daily emotion rows

The package does not require a specific database schema.

## 7. Add Auth

The FastAPI router intentionally does not enforce auth by default. Pass
`auth_hook` and verify the caller owns the requested `companion_id`.

## 8. Validate With Golden Tests

Run:

```bash
python -m pytest tests/golden
```

When event behavior changes intentionally, update the matching fixture and
document the contract change.

Event contract changes must also follow `docs/RELEASE_POLICY.md`. Patch and
minor releases must keep existing documented events backward compatible.

## Compatibility Notes

- `stream -> end` is the regular chat sequence.
- `name_reveal -> stream -> end` is the companion naming sequence.
- `user_name_set -> stream -> end` is the user-intro sequence.
- `coffee_request` short-circuits normal chat generation.
- Korean and English demo flows are covered by golden fixtures.
