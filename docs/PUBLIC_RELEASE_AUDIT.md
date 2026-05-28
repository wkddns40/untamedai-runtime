# Public Release Audit

Date: 2026-05-28

This checklist records the public-safety checks run before release work
continues. It is not a substitute for GitHub secret scanning or maintainer
review, but it documents the local gate used for this repository.

## Results

| Check | Result |
| --- | --- |
| Secret scan with `gitleaks dir . --no-banner --redact --verbose` | Passed, no leaks found. |
| Tracked secret/generator artifacts | Passed. Only `.env.example` is tracked intentionally. |
| Ignored local artifacts outside `.venv` | Passed after removing repo-local cache directories. |
| Private/internal path search | Passed. No private project paths found. |
| Operational identifier search | Passed. Findings are placeholders or scanner config only. |
| License notice | Passed. `LICENSE` contains MIT terms. |
| Package metadata license | Passed. `pyproject.toml` declares `license = "MIT"`. |

## Allowed Findings

The audit searches intentionally match a few safe placeholders:

- `.env.example` contains empty variable names such as `OPENAI_API_KEY=`,
  `SUPABASE_URL=`, and `SUPABASE_ANON_KEY=`.
- `.gitleaks.toml` contains scanner rule names and regexes for Supabase, OpenAI,
  and Polar-style secret detection.
- README files mention the demo path
  `examples/demo_showcase/backend/app.py`.
- README out-of-scope text mentions service role keys as content that must not
  be committed.

## Cleanup

Removed repo-local generated directories:

- `.pytest_cache`
- `.ruff_cache`
- `.mypy_cache`
- `__pycache__` directories under `src`, `tests`, and `examples`

`.venv` remains ignored and is not part of the public package contents.

## Commands

```bash
gitleaks dir . --no-banner --redact --verbose
python -m pytest
python -m ruff check .
python -m mypy src
```
