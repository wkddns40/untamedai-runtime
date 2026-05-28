# Untamed Companion Runtime

Public package skeleton for a LangGraph-based companion runtime.

This repository is intentionally separate from the private product repository.
It starts with no private git history and should only contain reusable runtime
code, examples, tests, and documentation approved for public release.

## Current Status

Package skeleton only. Runtime implementation begins in the next phase.

## License

MIT.

## Intended Scope

- LangGraph chat graph runtime
- naming ceremony state machine
- SSE event adapter
- store/provider interfaces
- in-memory demo and tests
- optional FastAPI, Supabase, and Postgres integrations

## Out of Scope

- product frontend
- private prompts and brand copy
- production deployment config
- billing/webhooks
- service role keys or project-specific environment values
