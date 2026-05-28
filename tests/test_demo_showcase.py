import importlib.util
from pathlib import Path
from types import ModuleType

from fastapi.testclient import TestClient

from untamed_companion.sse import parse_sse_frame

APP_PATH = (
    Path(__file__).resolve().parents[1]
    / "examples"
    / "demo_showcase"
    / "backend"
    / "app.py"
)


def _load_demo_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("demo_showcase_app", APP_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load demo app module.")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _client() -> TestClient:
    module = _load_demo_module()
    return TestClient(module.create_demo_app())


def _events(text: str) -> list[dict[str, object]]:
    frames = [frame for frame in text.split("\n\n") if frame.strip()]
    return [dict(parse_sse_frame(frame)) for frame in frames]


def test_demo_serves_static_ui() -> None:
    client = _client()

    response = client.get("/demo")
    script = client.get("/demo/assets/app.js")

    assert response.status_code == 200
    assert "Untamed Runtime Demo" in response.text
    assert script.status_code == 200
    assert "readEventStream" in script.text
    assert 'type === "stream" || type === "end"' not in script.text


def test_demo_showcase_scenario_endpoints() -> None:
    client = _client()

    assert client.post("/api/demo/reset/demo").status_code == 200

    greeting = client.get("/api/chat/demo/greeting?lang=en")
    assert [event["type"] for event in _events(greeting.text)] == ["greeting"]

    naming = client.post(
        "/api/chat/demo/stream",
        json={"message": "your name is Luna"},
        headers={"X-Chat-Canary": "graph"},
    )
    assert [event["type"] for event in _events(naming.text)] == [
        "name_reveal",
        "stream",
        "end",
    ]

    user_intro = client.post(
        "/api/chat/demo/stream",
        json={"message": "my name is Min"},
        headers={"X-Chat-Canary": "graph"},
    )
    assert [event["type"] for event in _events(user_intro.text)] == [
        "user_name_set",
        "stream",
        "end",
    ]

    coffee = client.post(
        "/api/chat/demo/stream",
        json={"message": "coffee", "type": "coffee_turn"},
        headers={"X-Chat-Canary": "graph"},
    )
    assert [event["type"] for event in _events(coffee.text)] == ["coffee_request"]

    emotion = client.post("/api/demo/emotion/demo")
    state = client.get("/api/demo/state/demo").json()

    assert emotion.status_code == 200
    assert emotion.json()["result"]["skipped"] is False
    assert state["companion"]["name"] == "Luna"
    assert state["companion"]["user_name"] == "Min"
    assert state["emotions"][0]["primary_emotion"] == "calm"
    assert state["metrics"]


def test_demo_reset_clears_session_state() -> None:
    client = _client()

    client.post("/api/chat/demo/stream", json={"message": "your name is Luna"})
    reset = client.post("/api/demo/reset/demo")

    assert reset.status_code == 200
    assert reset.json()["companion"]["name"] == "???"
    assert reset.json()["history"] == []
