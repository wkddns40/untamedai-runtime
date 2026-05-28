"""Public-safe chat graph nodes."""

from __future__ import annotations

import re

from untamed_companion.graph.events import CompanionEvent, event
from untamed_companion.graph.runtime import GraphRuntime
from untamed_companion.graph.state import ChatState

_NONE_INTENT = {"intent": "none", "name": None}
_COFFEE_TEXT = "I could use a warm cup of coffee."
_NAMING_PROMPT = "I think I am ready for a name. What would you like to call me?"


def _clean_name(raw: str | None) -> str | None:
    if raw is None:
        return None
    name = re.sub(r"[^\w\- ]", "", raw, flags=re.UNICODE).strip()
    if not name or len(name) > 32:
        return None
    return name


def _extract_user_name(message: str) -> str | None:
    patterns = (
        r"(?:my name is|i am|i'm|call me)\s+([A-Za-z][\w\- ]{0,31})",
    )
    for pattern in patterns:
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            return _clean_name(match.group(1))
    return None


def _extract_ai_name(message: str) -> str | None:
    patterns = (
        r"(?:your name is|call you|i will call you)\s+([A-Za-z][\w\- ]{0,31})",
    )
    for pattern in patterns:
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            return _clean_name(match.group(1))
    return None


def _companion_named(companion: dict[str, object]) -> bool:
    name = str(companion.get("name") or "")
    return bool(name and name != "???")


async def load_session(state: ChatState, _runtime: GraphRuntime) -> dict[str, object]:
    """Normalize defaults at graph entry."""

    companion = dict(state.get("companion") or {})
    companion.setdefault("name", "???")
    phase = state.get("naming_phase")
    prompted = bool(state.get("naming_prompted", False))
    if _companion_named(companion):
        phase = "named"
        prompted = True
    elif phase not in ("unnamed_idle", "awaiting_response"):
        phase = "awaiting_response" if prompted else "unnamed_idle"
    return {
        "companion": companion,
        "user_lang": state.get("user_lang", "en"),
        "user_tier": state.get("user_tier", "FREE"),
        "msg_type": state.get("msg_type", "chat"),
        "naming_phase": phase,
        "naming_prompted": prompted,
        "emit": [],
    }


async def intake(_state: ChatState, _runtime: GraphRuntime) -> dict[str, object]:
    """Placeholder intake node for future embedding and validation hooks."""

    return {}


async def handle_coffee_turn(
    _state: ChatState, _runtime: GraphRuntime
) -> dict[str, object]:
    """Short-circuit coffee event."""

    return {"emit": [event("coffee_request", _COFFEE_TEXT)]}


async def handle_awaiting_naming(
    state: ChatState, _runtime: GraphRuntime
) -> dict[str, object]:
    """Resolve pending ceremony name if the user supplied one."""

    name = _extract_ai_name(state.get("last_user_message", "")) or _clean_name(
        state.get("last_user_message", "")
    )
    if not name:
        return {}
    companion = dict(state.get("companion") or {})
    companion["name"] = name
    confirmation = f"You can call me {name}."
    return {
        "companion": companion,
        "naming_phase": "named",
        "naming_prompted": True,
        "pending_ai_text": confirmation,
        "emit": [
            event("name_reveal", name),
            event("stream", confirmation),
            event("end", confirmation, intent="naming"),
        ],
    }


async def detect_naming_intent(
    state: ChatState, _runtime: GraphRuntime
) -> dict[str, object]:
    """Detect public demo naming intents without LLM calls."""

    message = state.get("last_user_message", "")
    if state.get("naming_phase") == "named":
        user_name = _extract_user_name(message)
        intent = (
            {"intent": "user_intro", "name": user_name}
            if user_name
            else _NONE_INTENT
        )
        return {"naming_intent": intent}
    ai_name = _extract_ai_name(message)
    if ai_name:
        return {"naming_intent": {"intent": "ai_naming", "name": ai_name}}
    user_name = _extract_user_name(message)
    if user_name:
        return {"naming_intent": {"intent": "user_intro", "name": user_name}}
    return {"naming_intent": dict(_NONE_INTENT)}


async def apply_ai_name(state: ChatState, _runtime: GraphRuntime) -> dict[str, object]:
    """Apply user-provided companion name."""

    name = _clean_name((state.get("naming_intent") or {}).get("name"))
    if not name:
        return {}
    companion = dict(state.get("companion") or {})
    companion["name"] = name
    confirmation = f"You can call me {name}."
    return {
        "companion": companion,
        "naming_phase": "named",
        "pending_ai_text": confirmation,
        "emit": [
            event("name_reveal", name),
            event("stream", confirmation),
            event("end", confirmation, intent="naming"),
        ],
    }


async def apply_user_name(
    state: ChatState, _runtime: GraphRuntime
) -> dict[str, object]:
    """Persist user display name in state."""

    name = _clean_name((state.get("naming_intent") or {}).get("name"))
    if not name or state.get("user_name"):
        return {}
    return {"user_name": name, "emit": [event("user_name_set", name)]}


async def retrieve_memory(
    state: ChatState, runtime: GraphRuntime
) -> dict[str, object]:
    """Public placeholder for memory retrieval."""

    lang = state.get("user_lang", "en") or "en"
    weather_info = await runtime.resolve_weather_provider().get_weather(
        location="Seoul",
        lang=lang,
    )
    return {
        "semantic_logs": [],
        "recent_logs": [],
        "emotions": [],
        "weather_info": weather_info,
    }


async def compose_prompt(state: ChatState, _runtime: GraphRuntime) -> dict[str, object]:
    """Compose a neutral public prompt."""

    companion = state.get("companion") or {}
    name = str(companion.get("name") or "Companion")
    user_name = state.get("user_name") or "friend"
    return {
        "system_prompt": (
            f"You are {name}, an emotionally adaptive AI companion. "
            f"Speak with {user_name} in a warm, concise way."
        )
    }


async def generate_response(
    state: ChatState, runtime: GraphRuntime
) -> dict[str, object]:
    """Generate response with injected or default responder."""

    text = await runtime.resolve_chat_responder().generate_chat_response(state)
    return {
        "pending_ai_text": text,
        "emit": [event("stream", text), event("end", text, intent="chat")],
    }


async def persist_messages(
    _state: ChatState, _runtime: GraphRuntime
) -> dict[str, object]:
    """Placeholder persistence node."""

    return {}


async def check_naming_ceremony(
    state: ChatState, _runtime: GraphRuntime
) -> dict[str, object]:
    """Optionally emit naming prompt for demos/tests."""

    if (
        state.get("force_naming_prompt")
        and state.get("naming_phase") == "unnamed_idle"
        and not state.get("naming_prompted")
    ):
        return {
            "naming_phase": "awaiting_response",
            "naming_prompted": True,
            "emit": [event("naming_prompt", _NAMING_PROMPT)],
        }
    return {}


def route_after_intake(state: ChatState) -> str:
    if state.get("msg_type") == "coffee_turn":
        return "handle_coffee_turn"
    if state.get("naming_phase") == "awaiting_response":
        return "handle_awaiting_naming"
    return "detect_naming_intent"


def route_after_awaiting(state: ChatState) -> str:
    if state.get("naming_phase") == "named":
        return "persist_messages"
    return "detect_naming_intent"


def route_naming_intent(state: ChatState) -> str:
    intent = (state.get("naming_intent") or {}).get("intent") or "none"
    if intent == "ai_naming":
        return "apply_ai_name"
    if intent == "user_intro":
        return "apply_user_name"
    return "retrieve_memory"


def emitted_types(state: ChatState) -> list[str]:
    """Return event types for tests and demos."""

    return [evt["type"] for evt in state.get("emit", [])]


__all__ = [
    "CompanionEvent",
    "apply_ai_name",
    "apply_user_name",
    "check_naming_ceremony",
    "compose_prompt",
    "detect_naming_intent",
    "emitted_types",
    "generate_response",
    "handle_awaiting_naming",
    "handle_coffee_turn",
    "intake",
    "load_session",
    "persist_messages",
    "retrieve_memory",
    "route_after_awaiting",
    "route_after_intake",
    "route_naming_intent",
]
