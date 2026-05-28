# FastAPI Auth Example

This example shows application-owned authorization around the public chat
router. The package does not authenticate requests by default.

Run:

```bash
pip install -e ".[fastapi,dev]"
uvicorn examples.fastapi_auth.app:app --reload
```

Call `http://127.0.0.1:8000/api/chat/demo/history` with an `X-Demo-Token`
header value of `demo-token`. Without the header, the route returns `401`.
