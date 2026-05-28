"""SSE adapter for graph-emitted companion events."""

from __future__ import annotations

import json
import time
from collections.abc import AsyncIterator, Callable, Iterable, Mapping
from dataclasses import dataclass
from typing import Any, cast

from untamed_companion.graph.events import CompanionEvent, EventType, event

_PUBLIC_GRAPH_NODE_NAMES = frozenset(
    {
        "load_session",
        "intake",
        "handle_coffee_turn",
        "handle_awaiting_naming",
        "detect_naming_intent",
        "apply_ai_name",
        "apply_user_name",
        "retrieve_memory",
        "compose_prompt",
        "generate_response",
        "persist_messages",
        "check_naming_ceremony",
        "generate_greeting",
        "analyze_emotion",
    }
)

_EVENT_TYPES: set[str] = {
    "stream",
    "end",
    "greeting",
    "name_reveal",
    "user_name_set",
    "naming_prompt",
    "coffee_request",
    "error",
}


@dataclass(frozen=True, slots=True)
class StreamMetrics:
    """Optional per-stream metrics payload."""

    route: str
    bucket: str
    status: str
    duration_ms: float
    event_counts: dict[str, int]


MetricHook = Callable[[StreamMetrics], None]


def normalize_event(payload: Mapping[str, object]) -> CompanionEvent:
    """Return a public event payload with known keys only."""

    raw_type = str(payload.get("type") or "error")
    event_type = cast(EventType, raw_type if raw_type in _EVENT_TYPES else "error")
    content = str(payload.get("content") or "")
    normalized: CompanionEvent = {"type": event_type, "content": content}
    intent = payload.get("intent")
    if intent is not None:
        normalized["intent"] = str(intent)
    if "emotion_color" in payload:
        color = payload.get("emotion_color")
        normalized["emotion_color"] = None if color is None else str(color)
    return normalized


def sse_event(payload: Mapping[str, object]) -> str:
    """Format a mapping as one SSE data frame."""

    normalized = normalize_event(payload)
    return f"data: {json.dumps(normalized, ensure_ascii=False)}\n\n"


def parse_sse_frame(frame: str) -> CompanionEvent:
    """Parse one SSE data frame produced by `sse_event`."""

    lines = [line for line in frame.splitlines() if line.startswith("data:")]
    if not lines:
        raise ValueError("SSE frame has no data line")
    raw = "\n".join(line.removeprefix("data:").strip() for line in lines)
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("SSE data is not a JSON object")
    return normalize_event(cast(dict[str, object], data))


def events_from_state(state: Mapping[str, object]) -> list[CompanionEvent]:
    """Extract public events from a graph state mapping."""

    raw_events = state.get("emit") or []
    if not isinstance(raw_events, list):
        return []
    events: list[CompanionEvent] = []
    for raw in raw_events:
        if isinstance(raw, Mapping):
            events.append(normalize_event(cast(Mapping[str, object], raw)))
    return events


def event_type_counts(events: Iterable[Mapping[str, object]]) -> dict[str, int]:
    """Count event types."""

    counts: dict[str, int] = {}
    for raw in events:
        event_type = str(raw.get("type") or "unknown")
        counts[event_type] = counts.get(event_type, 0) + 1
    return counts


def count_event_types(frame: str, counter: dict[str, int]) -> None:
    """Count one serialized SSE frame into an existing counter."""

    try:
        payload = parse_sse_frame(frame)
    except (ValueError, json.JSONDecodeError):
        return
    event_type = payload["type"]
    counter[event_type] = counter.get(event_type, 0) + 1


async def forward_state_sse(
    graph: Any,
    initial_state: Mapping[str, object],
    *,
    config: Mapping[str, object] | None = None,
) -> AsyncIterator[str]:
    """Invoke a graph once and yield serialized SSE frames from final state."""

    result = await graph.ainvoke(dict(initial_state), config=config)
    if not isinstance(result, Mapping):
        return
    for payload in events_from_state(cast(Mapping[str, object], result)):
        yield sse_event(payload)


async def forward_graph_events(
    graph: Any,
    initial_state: Mapping[str, object],
    *,
    config: Mapping[str, object] | None = None,
    node_names: Iterable[str] | None = None,
    version: str = "v2",
) -> AsyncIterator[CompanionEvent]:
    """Forward LangGraph event stream as public companion events."""

    allowed_nodes = set(node_names or _PUBLIC_GRAPH_NODE_NAMES)
    async for raw_event in graph.astream_events(
        dict(initial_state),
        config=config,
        version=version,
    ):
        if not isinstance(raw_event, Mapping):
            continue
        event_name = raw_event.get("event")
        name = str(raw_event.get("name") or "")
        data = raw_event.get("data") or {}
        if event_name == "on_custom_event" and name == "stream":
            if isinstance(data, Mapping):
                content = str(data.get("content") or "")
                if content:
                    yield event("stream", content)
            continue
        if event_name != "on_chain_end" or name not in allowed_nodes:
            continue
        if not isinstance(data, Mapping):
            continue
        output = data.get("output") or {}
        if not isinstance(output, Mapping):
            continue
        for payload in events_from_state(cast(Mapping[str, object], output)):
            yield payload


async def forward_graph_sse(
    graph: Any,
    initial_state: Mapping[str, object],
    *,
    config: Mapping[str, object] | None = None,
    node_names: Iterable[str] | None = None,
    version: str = "v2",
    route: str = "graph",
    bucket: str = "unknown",
    metric_hook: MetricHook | None = None,
) -> AsyncIterator[str]:
    """Forward LangGraph event stream as serialized SSE frames."""

    started = time.perf_counter()
    status = "ok"
    counts: dict[str, int] = {}
    try:
        async for payload in forward_graph_events(
            graph,
            initial_state,
            config=config,
            node_names=node_names,
            version=version,
        ):
            frame = sse_event(payload)
            count_event_types(frame, counts)
            yield frame
    except Exception:
        status = "error"
        frame = sse_event(event("error", "Graph stream failed."))
        count_event_types(frame, counts)
        yield frame
        raise
    finally:
        if metric_hook is not None:
            metric_hook(
                StreamMetrics(
                    route=route,
                    bucket=bucket,
                    status=status,
                    duration_ms=round((time.perf_counter() - started) * 1000, 2),
                    event_counts=dict(counts),
                )
            )


async def collect_sse_frames(
    frames: AsyncIterator[str],
) -> list[str]:
    """Collect an async SSE frame iterator for tests."""

    return [frame async for frame in frames]
