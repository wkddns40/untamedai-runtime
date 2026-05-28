# Examples

- [Demo showcase](demo_showcase/)
- [FastAPI auth hook](fastapi_auth/)
- [Provider and prompt override](provider_prompt_override/)

## Demo Showcase

```bash
pip install -e ".[fastapi,dev]"
python examples/demo_showcase/backend/app.py
```

Open `http://127.0.0.1:8000/demo`.

Included:

- public FastAPI chat router
- static SSE inspector UI
- in-memory companion store
- deterministic fake providers
- backend-provided scenario presets
- reset endpoint
- daily emotion dry-run endpoint

## Provider And Prompt Override

```bash
pip install -e ".[dev]"
python examples/provider_prompt_override/app.py
```

Included:

- app-owned provider object
- app-owned prompt provider
- in-memory store
- public chat graph builder

## FastAPI Auth Hook

```bash
pip install -e ".[fastapi,dev]"
uvicorn examples.fastapi_auth.app:app --reload
```

Open `http://127.0.0.1:8000/api/chat/demo/history` with:

```text
X-Demo-Token: demo-token
```
