"""Public SSE-compatible event payloads."""

from __future__ import annotations

from typing import Literal, TypedDict

EventType = Literal[
    "stream",
    "end",
    "greeting",
    "name_reveal",
    "user_name_set",
    "naming_prompt",
    "coffee_request",
    "error",
]


class CompanionEvent(TypedDict, total=False):
    """Event emitted by graph nodes and forwarded by adapters."""

    type: EventType
    content: str
    intent: str
    emotion_color: str | None


def event(
    event_type: EventType,
    content: str = "",
    *,
    intent: str | None = None,
    emotion_color: str | None = None,
) -> CompanionEvent:
    """Create a typed event payload."""

    payload: CompanionEvent = {"type": event_type, "content": content}
    if intent is not None:
        payload["intent"] = intent
    if emotion_color is not None:
        payload["emotion_color"] = emotion_color
    return payload
