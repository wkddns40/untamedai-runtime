# Demo Showcase

The demo showcase is a local integration surface for package behavior. It uses
the public FastAPI router, public graph builders, deterministic fake providers,
and an in-memory store.

Run:

```bash
pip install -e ".[fastapi,dev]"
python examples/demo_showcase/backend/app.py
```

Open:

```text
http://127.0.0.1:8000/demo
```

## Demo Endpoints

- `GET /demo`: static showcase UI.
- `GET /api/demo/state/{companion_id}`: current companion, history, emotions,
  and stream metrics.
- `GET /api/demo/scenarios`: deterministic scenario presets consumed by the
  UI.
- `POST /api/demo/reset/{companion_id}`: clear in-memory demo state.
- `POST /api/demo/emotion/{companion_id}`: run the daily emotion graph against
  current in-memory history.

## Scenario Presets

The scenario endpoint returns ordered steps. The browser executes them through
the same public chat and greeting routes that a consumer app would call.

Current presets:

- `intro-en`: English greeting, AI naming, user naming, chat, emotion dry-run.
- `intro-ko`: Korean greeting, AI naming, user naming, chat, emotion dry-run.
- `coffee-en`: coffee-turn shortcut event.
- `coffee-ko`: Korean coffee-turn shortcut event.

## Event Inspector

The inspector renders:

- event order and type
- sanitized payload details
- event type counts
- stream metrics from `metric_hook`
- current in-memory state

For `end` events, the inspector displays completion status and `intent` only.
The event contract still carries normalized payload fields for downstream
consumers.

## Scope

The showcase is not production frontend code. It intentionally avoids private
prompts, product copy, external services, persistence credentials, and
authentication policy.
