"""FastAPI route factory for companion chat SSE endpoints."""

from __future__ import annotations

import inspect
from collections.abc import Awaitable, Callable, Mapping
from typing import Annotated, Any, Literal

try:
    from fastapi import APIRouter, Query, Request
    from fastapi.responses import StreamingResponse
    from pydantic import BaseModel, Field
except ImportError as exc:  # pragma: no cover - exercised by optional installs.
    from untamed_companion.exceptions import IntegrationNotConfiguredError

    raise IntegrationNotConfiguredError(
        "FastAPI integration requires `pip install untamedai-runtime[fastapi]`."
    ) from exc

from untamed_companion.graph import (
    GraphRuntime,
    build_chat_graph,
    build_greeting_graph,
)
from untamed_companion.sse import MetricHook, forward_graph_sse

AuthHook = Callable[[Request, str], None | Awaitable[None]]
ConfigFactory = Callable[[str], Mapping[str, object] | None]


class ChatRequest(BaseModel):
    """Request body for chat stream turns."""

    message: str = Field(min_length=1)
    user_name: str = ""
    lang: Literal["ko", "en"] = "en"
    type: Literal["chat", "coffee_turn", "set_lang"] = "chat"
    companion: dict[str, object] | None = None


def _default_config(companion_id: str) -> dict[str, object]:
    return {"configurable": {"thread_id": companion_id}}


async def _maybe_await(value: None | Awaitable[None]) -> None:
    if inspect.isawaitable(value):
        await value


async def _authorize(
    hook: AuthHook | None,
    request: Request,
    companion_id: str,
) -> None:
    if hook is None:
        return
    await _maybe_await(hook(request, companion_id))


def _bucket_from_request(request: Request) -> str:
    raw = request.headers.get("x-chat-canary") or "unknown"
    return raw if raw in {"graph", "legacy", "unknown"} else "unknown"


async def _companion_from_store(
    runtime: GraphRuntime,
    companion_id: str,
) -> dict[str, object]:
    store = runtime.resolve_companion_store()
    if store is None:
        return {"name": "???"}
    record = await store.get_companion(companion_id)
    return dict(record or {"name": "???"})


def create_chat_router(
    runtime: GraphRuntime | None = None,
    *,
    prefix: str = "",
    auth_hook: AuthHook | None = None,
    metric_hook: MetricHook | None = None,
    config_factory: ConfigFactory | None = None,
) -> APIRouter:
    """Create a FastAPI router exposing public companion chat endpoints.

    Routes:
    - `GET /chat/{companion_id}/history`
    - `GET /chat/{companion_id}/greeting`
    - `POST /chat/{companion_id}/stream`

    Auth is intentionally not built in. Consumers can pass `auth_hook` to
    enforce ownership, API keys, sessions, or any app-specific policy.
    """

    active_runtime = runtime or GraphRuntime()
    router = APIRouter(prefix=prefix)
    resolve_config = config_factory or _default_config

    @router.get("/chat/{companion_id}/history")
    async def chat_history(
        companion_id: str,
        request: Request,
        limit: Annotated[int, Query(ge=1, le=100)] = 30,
    ) -> list[dict[str, object]]:
        await _authorize(auth_hook, request, companion_id)
        store = active_runtime.resolve_companion_store()
        if store is None:
            return []
        rows = await store.get_recent_chat(companion_id, limit=limit)
        return [dict(row) for row in rows]

    @router.get("/chat/{companion_id}/greeting")
    async def chat_greeting(
        companion_id: str,
        request: Request,
        lang: Literal["ko", "en"] = "en",
    ) -> StreamingResponse:
        await _authorize(auth_hook, request, companion_id)
        graph = build_greeting_graph(runtime=active_runtime)
        companion = await _companion_from_store(active_runtime, companion_id)
        initial_state = {
            "companion_id": companion_id,
            "user_lang": lang,
            "companion": companion,
        }
        frames = forward_graph_sse(
            graph,
            initial_state,
            config=resolve_config(f"greeting:{companion_id}"),
            route="/chat/greeting",
            bucket=_bucket_from_request(request),
            metric_hook=metric_hook,
        )
        return StreamingResponse(
            frames,
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
        )

    @router.post("/chat/{companion_id}/stream")
    async def chat_stream(
        companion_id: str,
        body: ChatRequest,
        request: Request,
    ) -> StreamingResponse:
        await _authorize(auth_hook, request, companion_id)
        graph = build_chat_graph(runtime=active_runtime)
        initial_state: dict[str, Any] = {
            "companion_id": companion_id,
            "last_user_message": body.message,
            "user_name": body.user_name,
            "user_lang": body.lang,
            "msg_type": body.type,
        }
        if body.companion is not None:
            initial_state["companion"] = body.companion
        frames = forward_graph_sse(
            graph,
            initial_state,
            config=resolve_config(companion_id),
            route="/chat/stream",
            bucket=_bucket_from_request(request),
            metric_hook=metric_hook,
        )
        return StreamingResponse(
            frames,
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
        )

    return router
