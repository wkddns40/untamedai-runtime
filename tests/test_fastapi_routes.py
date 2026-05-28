import asyncio
from collections.abc import Sequence

from fastapi import FastAPI, HTTPException, Request
from fastapi.testclient import TestClient

from untamed_companion.fastapi import ChatRouterSettings, create_chat_router
from untamed_companion.graph import GraphRuntime
from untamed_companion.sse import StreamMetrics, parse_sse_frame
from untamed_companion.store import InMemoryCompanionStore


def _client(runtime: GraphRuntime | None = None) -> TestClient:
    app = FastAPI()
    app.include_router(create_chat_router(runtime=runtime))
    return TestClient(app)


def _events(text: str) -> list[dict[str, object]]:
    frames = [frame for frame in text.split("\n\n") if frame.strip()]
    return [dict(parse_sse_frame(frame)) for frame in frames]


def _event_types(events: Sequence[dict[str, object]]) -> list[object]:
    return [event["type"] for event in events]


def test_history_returns_empty_without_store() -> None:
    client = _client()
    response = client.get("/chat/cid/history")

    assert response.status_code == 200
    assert response.json() == []


def test_history_rejects_invalid_limit() -> None:
    client = _client()
    response = client.get("/chat/cid/history?limit=0")

    assert response.status_code == 422


def test_history_returns_store_rows() -> None:
    store = InMemoryCompanionStore()
    asyncio.run(store.add_chat_log("cid", sender="USER", message="hello"))
    app = FastAPI()

    app.include_router(create_chat_router(runtime=GraphRuntime(companion_store=store)))
    with TestClient(app) as client:
        response = client.get("/chat/cid/history")

    assert response.status_code == 200
    assert response.json()[0]["message"] == "hello"


def test_greeting_route_streams_sse() -> None:
    store = InMemoryCompanionStore()
    asyncio.run(store.put_companion("cid", {"name": "Luna"}))
    app = FastAPI()

    app.include_router(create_chat_router(runtime=GraphRuntime(companion_store=store)))
    with TestClient(app) as client:
        response = client.get("/chat/cid/greeting?lang=en")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert _event_types(_events(response.text)) == ["greeting"]


def test_stream_route_preserves_naming_order() -> None:
    client = _client()
    response = client.post(
        "/chat/cid/stream",
        json={
            "message": "your name is Luna",
            "companion": {"name": "???"},
        },
    )
    events = _events(response.text)

    assert response.status_code == 200
    assert _event_types(events) == ["name_reveal", "stream", "end"]
    assert events[-1]["intent"] == "naming"


def test_stream_route_emits_metrics() -> None:
    metrics: list[StreamMetrics] = []
    app = FastAPI()
    app.include_router(
        create_chat_router(
            runtime=GraphRuntime(),
            metric_hook=metrics.append,
        )
    )
    client = TestClient(app)

    response = client.post(
        "/chat/cid/stream",
        json={"message": "coffee", "type": "coffee_turn"},
        headers={"X-Chat-Canary": "graph"},
    )

    assert response.status_code == 200
    assert _event_types(_events(response.text)) == ["coffee_request"]
    assert metrics[0].route == "/chat/stream"
    assert metrics[0].bucket == "graph"
    assert metrics[0].event_counts == {"coffee_request": 1}


def test_stream_route_uses_custom_bucket_resolver() -> None:
    metrics: list[StreamMetrics] = []
    app = FastAPI()
    app.include_router(
        create_chat_router(
            runtime=GraphRuntime(),
            metric_hook=metrics.append,
            bucket_resolver=lambda _request: "stable",
        )
    )
    client = TestClient(app)

    response = client.post(
        "/chat/cid/stream",
        json={"message": "coffee", "type": "coffee_turn"},
        headers={"X-Chat-Canary": "legacy"},
    )

    assert response.status_code == 200
    assert metrics[0].bucket == "stable"


def test_auth_hook_blocks_request() -> None:
    def auth_hook(_request: Request, _companion_id: str) -> None:
        raise HTTPException(status_code=403, detail="forbidden")

    app = FastAPI()
    app.include_router(create_chat_router(auth_hook=auth_hook))
    client = TestClient(app)
    response = client.get("/chat/cid/history")

    assert response.status_code == 403
    assert response.json()["detail"] == "forbidden"


def test_async_auth_hook_receives_companion_id() -> None:
    calls: list[str] = []

    async def auth_hook(_request: Request, companion_id: str) -> None:
        calls.append(companion_id)

    app = FastAPI()
    app.include_router(create_chat_router(auth_hook=auth_hook))
    client = TestClient(app)
    response = client.get("/chat/cid/history")

    assert response.status_code == 200
    assert calls == ["cid"]


def test_config_factory_receives_route_thread_id() -> None:
    calls: list[str] = []

    def config_factory(thread_id: str) -> dict[str, object]:
        calls.append(thread_id)
        return {"configurable": {"thread_id": f"custom:{thread_id}"}}

    app = FastAPI()
    app.include_router(create_chat_router(config_factory=config_factory))
    client = TestClient(app)
    response = client.get("/chat/cid/greeting?lang=en")

    assert response.status_code == 200
    assert calls == ["greeting:cid"]


def test_router_settings_control_history_limit() -> None:
    store = InMemoryCompanionStore()
    asyncio.run(store.add_chat_log("cid", sender="USER", message="first"))
    asyncio.run(store.add_chat_log("cid", sender="USER", message="second"))
    app = FastAPI()
    app.include_router(
        create_chat_router(
            runtime=GraphRuntime(companion_store=store),
            settings=ChatRouterSettings(history_limit_default=1, history_limit_max=2),
        )
    )
    client = TestClient(app)

    default_response = client.get("/chat/cid/history")
    invalid_response = client.get("/chat/cid/history?limit=3")

    assert default_response.status_code == 200
    assert len(default_response.json()) == 1
    assert invalid_response.status_code == 422


def test_router_settings_control_sse_headers() -> None:
    app = FastAPI()
    app.include_router(
        create_chat_router(
            settings=ChatRouterSettings(
                sse_headers={
                    "Cache-Control": "no-store",
                    "X-Accel-Buffering": "no",
                }
            )
        )
    )
    client = TestClient(app)

    response = client.get("/chat/cid/greeting?lang=en")

    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["x-accel-buffering"] == "no"


def test_router_settings_reject_invalid_history_limits() -> None:
    try:
        ChatRouterSettings(history_limit_default=3, history_limit_max=2)
    except ValueError as exc:
        assert str(exc) == "history_limit_default must be <= history_limit_max"
    else:  # pragma: no cover
        raise AssertionError("expected invalid history limit settings")


def test_router_prefix() -> None:
    app = FastAPI()
    app.include_router(create_chat_router(prefix="/api"))
    client = TestClient(app)
    response = client.get("/api/chat/cid/history")

    assert response.status_code == 200
