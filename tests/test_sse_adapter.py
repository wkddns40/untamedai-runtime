import pytest

from untamed_companion.graph import build_chat_graph, build_greeting_graph
from untamed_companion.graph.events import event
from untamed_companion.sse import (
    StreamMetrics,
    collect_sse_frames,
    count_event_types,
    event_type_counts,
    events_from_state,
    forward_graph_sse,
    forward_state_sse,
    parse_sse_frame,
    sse_event,
)


def test_sse_event_roundtrip() -> None:
    frame = sse_event(event("end", "done", intent="chat"))
    parsed = parse_sse_frame(frame)

    assert frame.startswith("data: ")
    assert parsed == {"type": "end", "content": "done", "intent": "chat"}


def test_events_from_state_normalizes_unknown_type() -> None:
    events = events_from_state({"emit": [{"type": "unknown", "content": "x"}]})

    assert events == [{"type": "error", "content": "x"}]


def test_event_type_counts_and_frame_counter() -> None:
    counts: dict[str, int] = {}
    count_event_types(sse_event(event("stream", "a")), counts)
    count_event_types(sse_event(event("end", "b", intent="chat")), counts)

    assert counts == {"stream": 1, "end": 1}
    assert event_type_counts(
        [event("stream", "a"), event("stream", "b")]
    ) == {"stream": 2}


async def test_forward_state_sse_preserves_chat_event_order() -> None:
    graph = build_chat_graph()
    frames = await collect_sse_frames(
        forward_state_sse(
            graph,
            {
                "companion_id": "demo",
                "last_user_message": "hello",
                "companion": {"name": "Luna"},
            },
        )
    )
    events = [parse_sse_frame(frame) for frame in frames]

    assert [payload["type"] for payload in events] == ["stream", "end"]
    assert events[-1]["intent"] == "chat"


async def test_forward_graph_sse_preserves_naming_event_order() -> None:
    graph = build_chat_graph()
    frames = await collect_sse_frames(
        forward_graph_sse(
            graph,
            {
                "companion_id": "demo",
                "last_user_message": "your name is Luna",
                "companion": {"name": "???"},
            },
        )
    )
    events = [parse_sse_frame(frame) for frame in frames]

    assert [payload["type"] for payload in events] == [
        "name_reveal",
        "stream",
        "end",
    ]
    assert events[-1]["intent"] == "naming"


async def test_forward_graph_sse_supports_greeting_graph() -> None:
    graph = build_greeting_graph()
    frames = await collect_sse_frames(
        forward_graph_sse(graph, {"companion": {"name": "Luna"}})
    )

    assert [parse_sse_frame(frame)["type"] for frame in frames] == ["greeting"]


async def test_forward_graph_sse_metric_hook_counts_events() -> None:
    graph = build_chat_graph()
    metrics: list[StreamMetrics] = []
    frames = await collect_sse_frames(
        forward_graph_sse(
            graph,
            {
                "companion_id": "demo",
                "last_user_message": "coffee",
                "msg_type": "coffee_turn",
            },
            route="/chat",
            bucket="graph",
            metric_hook=metrics.append,
        )
    )

    assert [parse_sse_frame(frame)["type"] for frame in frames] == ["coffee_request"]
    assert metrics[0].route == "/chat"
    assert metrics[0].bucket == "graph"
    assert metrics[0].status == "ok"
    assert metrics[0].event_counts == {"coffee_request": 1}


async def test_forward_graph_sse_raises_after_error_frame() -> None:
    class BrokenGraph:
        async def astream_events(self, *_args: object, **_kwargs: object):
            raise RuntimeError("boom")
            yield {}

    frames: list[str] = []
    with pytest.raises(RuntimeError):
        async for frame in forward_graph_sse(BrokenGraph(), {}):
            frames.append(frame)

    assert [parse_sse_frame(frame)["type"] for frame in frames] == ["error"]
