"""FastAPI auth-hook example for `untamedai-runtime`."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request

from untamed_companion.fastapi import ChatRouterSettings, create_chat_router
from untamed_companion.graph import GraphRuntime
from untamed_companion.store import InMemoryCompanionStore

app = FastAPI()


async def require_demo_token(request: Request, companion_id: str) -> None:
    """Example only: replace with app-owned session or tenant checks."""

    token = request.headers.get("x-demo-token")
    if token != "demo-token":
        raise HTTPException(status_code=401, detail="missing or invalid token")
    if companion_id == "forbidden":
        raise HTTPException(status_code=403, detail="companion access denied")


runtime = GraphRuntime(companion_store=InMemoryCompanionStore())

app.include_router(
    create_chat_router(
        runtime=runtime,
        prefix="/api",
        auth_hook=require_demo_token,
        settings=ChatRouterSettings(history_limit_default=20, history_limit_max=50),
    )
)
