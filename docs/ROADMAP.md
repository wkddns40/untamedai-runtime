# Roadmap

This roadmap describes expected public package direction after `v0.1.1`. It is
not a guarantee of dates or exact scope.

## 0.1.x

Focus: alpha release hygiene.

- Keep PyPI, TestPyPI, GitHub tag, and GitHub release artifacts aligned.
- Fix packaging, documentation, and demo issues through patch releases.
- Avoid public behavior changes unless they are backward compatible.

## 0.2.0

Focus: FastAPI route factory hardening.

- Stabilize `create_chat_router(...)` parameters.
- Add more examples for `auth_hook` and application-owned authorization.
- Document router extension points and non-FastAPI transport usage.
- Keep current SSE event ordering compatible.

## 0.3.0

Focus: optional persistence integrations.

- Harden `SupabaseCompanionStore` behavior behind the `supabase` extra.
- Expand Postgres/checkpointer guidance behind the `postgres` extra.
- Add migration snippets without publishing production application schema.
- Keep core install free of Supabase and Postgres dependencies.

## 0.4.0

Focus: richer integration showcase and docs.

- Expand demo scenarios while keeping the demo product-neutral.
- Add more event inspector coverage.
- Add consumer-facing examples for provider and prompt overrides.
- Improve troubleshooting docs for common integration failures.

## 1.0.0

Focus: stable public API.

- Declare stable SSE event contract.
- Declare stable store/provider protocols.
- Declare stable FastAPI route factory API.
- Publish upgrade guide from alpha versions.
- Move breaking changes to future major versions only.

## Compatibility Rules

- Patch releases must be backward compatible.
- Event contract changes require migration documentation.
- Public API removals require a deprecation path unless a security issue makes
  immediate removal necessary.
- Private prompts, product frontend code, production deployment config, billing,
  and secrets remain out of scope.
