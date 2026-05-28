# Release Policy

This project uses semantic versioning. The public compatibility surface is the
Python API, optional extras, SSE event contract, store/provider/prompt
protocols, and FastAPI route factory.

## Versioning

Current status: stable since `1.0.0`.

- Patch releases fix docs, packaging, tests, and backward-compatible behavior.
- Minor releases may add public APIs or new backward-compatible behavior.
- Breaking changes are not allowed in patch or minor releases.
- If a breaking change is unavoidable, first add a compatibility path, document
  the migration, and remove the old behavior only in a major release.
- Breaking changes require a major version.

## Public Contract

These surfaces are treated as public:

- `untamed_companion.graph`
- `untamed_companion.sse`
- `untamed_companion.store`
- `untamed_companion.providers`
- `untamed_companion.prompts`
- `untamed_companion.fastapi`
- `untamed_companion.checkpoint`
- SSE event types and payload fields documented in `docs/EVENT_CONTRACT.md`
- Optional extras declared in `pyproject.toml`
- Release documentation in `docs/API_STABILITY.md`

Internal implementation details may change when public behavior remains the
same.

## Event Contract Changes

The SSE event contract is the most important runtime integration surface.

Any intentional event contract change requires:

- an update to `docs/EVENT_CONTRACT.md`
- an update to `docs/MIGRATION.md`
- a changelog entry
- golden fixture updates under `tests/golden/fixtures`
- a version bump that matches the compatibility impact

Patch releases must not remove event types, rename event types, or change the
meaning of existing event fields.

## Deprecation

When possible, public APIs should be deprecated before removal.

Deprecation notes should include:

- first deprecated version
- replacement API or migration path
- earliest removal version

## Release Checklist

Before publishing a release:

```bash
python -m pytest
python -m ruff check .
python -m mypy src
gitleaks dir . --no-banner --redact --verbose
python -m build
python -m twine check dist/*
```

Then publish through GitHub Actions Trusted Publishing:

1. Publish to TestPyPI.
2. Install from TestPyPI in a fresh environment.
3. Approve the `pypi` environment deployment.
4. Publish to PyPI.
5. Install from PyPI in a fresh environment.
6. Confirm GitHub release assets match PyPI artifact digests.

## Failed Release Handling

Published package files are immutable. If a PyPI release has a defect, prefer a
new patch release. Yank the broken release only when users should stop selecting
it through normal dependency resolution.

Do not delete and recreate public release history as a substitute for a patch
release once an artifact is published to PyPI.
