"""Demo showcase app for the public runtime package."""

from __future__ import annotations

import os
from collections.abc import Sequence
from dataclasses import asdict
from datetime import UTC, date, datetime
from pathlib import Path

try:
    from fastapi import FastAPI
    from fastapi.responses import FileResponse, RedirectResponse
    from fastapi.staticfiles import StaticFiles
except ImportError as exc:  # pragma: no cover - optional example dependency.
    from untamed_companion.exceptions import IntegrationNotConfiguredError

    raise IntegrationNotConfiguredError(
        "Demo showcase requires `pip install -e .[fastapi,dev]`."
    ) from exc

from untamed_companion.fastapi import create_chat_router
from untamed_companion.graph import GraphRuntime, build_emotion_graph
from untamed_companion.providers import FakeEmbeddingProvider, FakeLLMProvider
from untamed_companion.providers.weather import StaticWeatherProvider
from untamed_companion.sse import StreamMetrics
from untamed_companion.store import InMemoryCompanionStore
from untamed_companion.store.base import EmotionLog

ROOT_DIR = Path(__file__).resolve().parents[1]
STATIC_DIR = ROOT_DIR / "static"
DEFAULT_COMPANION_ID = "demo"
DEMO_SCENARIOS: tuple[dict[str, object], ...] = (
    {
        "id": "intro-en",
        "label": "Intro EN",
        "lang": "en",
        "steps": [
            {"action": "greeting"},
            {"action": "chat", "message": "your name is Luna"},
            {"action": "chat", "message": "my name is Min"},
            {"action": "chat", "message": "hello"},
            {"action": "emotion"},
        ],
    },
    {
        "id": "intro-ko",
        "label": "Intro KO",
        "lang": "ko",
        "steps": [
            {"action": "greeting"},
            {"action": "chat", "message": "네 이름은 루나"},
            {"action": "chat", "message": "내 이름은 민"},
            {"action": "chat", "message": "안녕"},
            {"action": "emotion"},
        ],
    },
    {
        "id": "coffee-en",
        "label": "Coffee EN",
        "lang": "en",
        "steps": [
            {"action": "chat", "message": "coffee", "type": "coffee_turn"},
        ],
    },
)


def _today_iso() -> str:
    return datetime.now(UTC).date().isoformat()


async def _snapshot(
    store: InMemoryCompanionStore,
    metrics: Sequence[StreamMetrics],
    companion_id: str,
) -> dict[str, object]:
    companion = await store.get_companion(companion_id)
    history = await store.get_recent_chat(companion_id, limit=20)
    emotions = await store.get_emotions(companion_id, limit=5)
    return {
        "companion_id": companion_id,
        "companion": companion or {"name": "???"},
        "history": history,
        "emotions": emotions,
        "metrics": [asdict(metric) for metric in metrics[-10:]],
    }


async def _run_emotion_dry_run(
    runtime: GraphRuntime,
    store: InMemoryCompanionStore,
    companion_id: str,
    target_date: date,
) -> dict[str, object]:
    logs = await store.get_recent_chat(companion_id, limit=20)
    graph = build_emotion_graph(runtime=runtime)
    result = await graph.ainvoke(
        {
            "companion_id": companion_id,
            "target_date": target_date.isoformat(),
            "logs": logs,
        }
    )
    if not result.get("skipped"):
        analysis = dict(result.get("analysis") or {})
        await store.put_emotion(
            companion_id,
            date=target_date.isoformat(),
            values=EmotionLog(**analysis),
        )
    return dict(result)


def create_demo_app() -> FastAPI:
    """Create a self-contained FastAPI app for the runtime showcase."""

    store = InMemoryCompanionStore()
    metrics: list[StreamMetrics] = []
    runtime = GraphRuntime(
        llm_provider=FakeLLMProvider(),
        embedding_provider=FakeEmbeddingProvider(dimensions=8),
        weather_provider=StaticWeatherProvider("Clear demo weather, 21C."),
        companion_store=store,
    )
    app = FastAPI(title="Untamed Runtime Demo", version="0.4.0")
    app.state.demo_store = store
    app.state.demo_runtime = runtime
    app.state.demo_metrics = metrics

    app.include_router(
        create_chat_router(
            runtime=runtime,
            prefix="/api",
            metric_hook=metrics.append,
        )
    )
    app.mount(
        "/demo/assets",
        StaticFiles(directory=STATIC_DIR),
        name="demo-assets",
    )

    @app.get("/", include_in_schema=False)
    async def root() -> RedirectResponse:
        return RedirectResponse("/demo")

    @app.get("/demo", include_in_schema=False)
    async def demo() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html")

    @app.get("/api/demo/state")
    async def default_demo_state() -> dict[str, object]:
        return await _snapshot(store, metrics, DEFAULT_COMPANION_ID)

    @app.get("/api/demo/state/{companion_id}")
    async def demo_state(companion_id: str) -> dict[str, object]:
        return await _snapshot(store, metrics, companion_id)

    @app.get("/api/demo/scenarios")
    async def demo_scenarios() -> list[dict[str, object]]:
        return [dict(scenario) for scenario in DEMO_SCENARIOS]

    @app.post("/api/demo/reset")
    async def default_reset_demo() -> dict[str, object]:
        return await reset_demo(DEFAULT_COMPANION_ID)

    @app.post("/api/demo/reset/{companion_id}")
    async def reset_demo(companion_id: str) -> dict[str, object]:
        store.companions.pop(companion_id, None)
        store.chat_logs.pop(companion_id, None)
        store.emotions.pop(companion_id, None)
        metrics.clear()
        return await _snapshot(store, metrics, companion_id)

    @app.post("/api/demo/emotion")
    async def default_emotion_demo() -> dict[str, object]:
        return await emotion_demo(DEFAULT_COMPANION_ID)

    @app.post("/api/demo/emotion/{companion_id}")
    async def emotion_demo(companion_id: str) -> dict[str, object]:
        result = await _run_emotion_dry_run(
            runtime,
            store,
            companion_id,
            date.fromisoformat(_today_iso()),
        )
        return {
            "result": result,
            "state": await _snapshot(store, metrics, companion_id),
        }

    return app


app = create_demo_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host=os.environ.get("HOST", "127.0.0.1"),
        port=int(os.environ.get("PORT", "8000")),
    )
