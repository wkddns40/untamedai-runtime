# Changelog

All notable changes to this package will be documented here.

## Unreleased

No changes yet.

## 0.4.0 - 2026-05-28

- Expanded the demo showcase with backend-provided scenario presets.
- Added event inspector counts, sanitized event payload details, and live state
  rendering in the demo UI.
- Added a provider/prompt override example for consumer-owned integrations.
- Added demo showcase and troubleshooting documentation.

## 0.3.1 - 2026-05-28

- Hardened optional Supabase store configuration and fake-client testing.
- Added async Postgres checkpointer helper behind the `postgres` extra.
- Fixed the `postgres` extra to use `langgraph-checkpoint-postgres>=3,<4`,
  preserving compatibility with current LangGraph 1.x installs.
- Added persistence docs for Supabase table/RPC mapping and Postgres
  checkpointer setup.
- Kept core install free of Supabase and Postgres dependencies.

## 0.3.0 - 2026-05-28

- TestPyPI-only release candidate for optional persistence integrations.
- Superseded by `0.3.1` before PyPI publication because the initial
  `postgres` extra could resolve older LangGraph dependencies.

## 0.2.0 - 2026-05-28

- Stabilized FastAPI route factory extension points with `ChatRouterSettings`.
- Added custom metrics bucket resolution for FastAPI stream routes.
- Exported FastAPI integration callback types.
- Added auth-hook example app and expanded FastAPI integration docs.
- Documented non-FastAPI SSE transport usage.
- Added release policy and roadmap docs for package governance.
- Kept existing SSE event ordering backward compatible.

## 0.1.1 - 2026-05-28

- Added GitHub Actions Trusted Publishing workflow for TestPyPI and PyPI.
- Added GitHub environment gate guidance for PyPI release approval.
- Clarified alpha API stability and production authentication responsibility.
- Prepared PyPI alpha release from a matching source tag and artifact set.

## 0.1.0 - 2026-05-28

- Created public package repository skeleton.
- Added importable package namespace and development tool configuration.
- Added public-safe chat, greeting, and emotion graph builders.
- Added provider protocols with fake and optional OpenAI implementations.
- Added companion store protocol with in-memory and optional Supabase adapters.
- Added SSE adapter with graph forwarding, parsing, and optional metrics hook.
- Added FastAPI chat router factory for history, greeting, and stream routes.
- Added neutral prompt provider interface with static override support.
- Added demo showcase app with static SSE inspector and reset/emotion endpoints.
- Added Korean demo language toggle and Korean naming/user-name detection.
- Added public golden event contract tests and GitHub Actions CI matrix.
- Added README quickstart and architecture, event, integration, migration docs.
- Added public release audit notes and cleaned generated cache artifacts.
