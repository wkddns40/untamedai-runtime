# Examples

- [Demo showcase](demo_showcase/)
- [FastAPI auth hook](fastapi_auth/)

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
- reset endpoint
- daily emotion dry-run endpoint

## FastAPI Auth Hook

```bash
pip install -e ".[fastapi,dev]"
uvicorn examples.fastapi_auth.app:app --reload
```

Open `http://127.0.0.1:8000/api/chat/demo/history` with:

```text
X-Demo-Token: demo-token
```
