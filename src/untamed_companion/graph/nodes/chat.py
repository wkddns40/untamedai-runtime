"""Public-safe chat graph nodes."""

from __future__ import annotations

import re
from typing import cast

from untamed_companion.graph.events import CompanionEvent, event
from untamed_companion.graph.runtime import GraphRuntime
from untamed_companion.graph.state import ChatState
from untamed_companion.store.base import CompanionRecord

_NONE_INTENT = {"intent": "none", "name": None}
_COFFEE_TEXT = "I could use a warm cup of coffee."
_COFFEE_TEXT_KO = "따뜻한 커피 한 잔이 필요해요."
_NAMING_PROMPT = "I think I am ready for a name. What would you like to call me?"
_NAMING_PROMPT_KO = "이제 이름을 가져도 될 것 같아요. 저를 뭐라고 불러 줄래요?"
_NAME_PATTERN = r"([A-Za-z가-힣][\w가-힣\- ]{0,31}?)"


def _clean_name(raw: str | None) -> str | None:
    if raw is None:
        return None
    name = re.sub(r"[^\w\- ]", "", raw, flags=re.UNICODE).strip()
    if not name or len(name) > 32:
        return None
    return name


def _extract_user_name(message: str) -> str | None:
    patterns = (
        rf"(?:my name is|i am|i'm|call me)\s+{_NAME_PATTERN}$",
        rf"(?:내 이름은|제 이름은)\s*{_NAME_PATTERN}"
        r"(?:입니다|이에요|예요|이야|야)?$",
        rf"(?:나는|저는|난|전)\s*{_NAME_PATTERN}"
        r"(?:입니다|이에요|예요|이야|야)?$",
        rf"{_NAME_PATTERN}(?:라고|이라고)\s*(?:불러|불러줘|불러 주세요|불러주세요)",
    )
    for pattern in patterns:
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            return _clean_name(match.group(1))
    return None


def _extract_ai_name(message: str) -> str | None:
    patterns = (
        rf"(?:your name is|call you|i will call you)\s+{_NAME_PATTERN}$",
        rf"(?:네 이름은|너의 이름은|니 이름은|너 이름은)\s*{_NAME_PATTERN}"
        r"(?:입니다|이에요|예요|이야|야)?$",
        rf"(?:널|너를|너는)\s*{_NAME_PATTERN}(?:라고|이라고)\s*"
        r"(?:부를게|부를 거야|부르겠어|불러줄게)",
        rf"{_NAME_PATTERN}(?:라고|이라고)\s*"
        r"(?:부를게|부를 거야|부르겠어|불러줄게)",
    )
    for pattern in patterns:
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            return _clean_name(match.group(1))
    return None


def _companion_named(companion: dict[str, object]) -> bool:
    name = str(companion.get("name") or "")
    return bool(name and name != "???")


def _is_ko(state: ChatState) -> bool:
    return state.get("user_lang") == "ko"


def _name_confirmation(name: str, state: ChatState) -> str:
    if _is_ko(state):
        return f"저를 {name}라고 불러 주세요."
    return f"You can call me {name}."


async def load_session(state: ChatState, runtime: GraphRuntime) -> dict[str, object]:
    """Normalize defaults at graph entry."""

    companion_id = state.get("companion_id", "")
    companion = dict(state.get("companion") or {})
    store = runtime.resolve_companion_store()
    if not companion and store is not None and companion_id:
        stored = await store.get_companion(companion_id)
        companion = dict(stored or {})
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
        "user_name": state.get("user_name") or str(companion.get("user_name") or ""),
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
    state: ChatState, _runtime: GraphRuntime
) -> dict[str, object]:
    """Short-circuit coffee event."""

    content = _COFFEE_TEXT_KO if _is_ko(state) else _COFFEE_TEXT
    return {"emit": [event("coffee_request", content)]}


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
    confirmation = _name_confirmation(name, state)
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


async def apply_ai_name(state: ChatState, runtime: GraphRuntime) -> dict[str, object]:
    """Apply user-provided companion name."""

    name = _clean_name((state.get("naming_intent") or {}).get("name"))
    if not name:
        return {}
    companion_id = state.get("companion_id", "")
    companion = dict(state.get("companion") or {})
    companion["name"] = name
    store = runtime.resolve_companion_store()
    if store is not None and companion_id:
        await store.put_companion(
            companion_id,
            cast(CompanionRecord, {"name": name}),
        )
    confirmation = _name_confirmation(name, state)
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
    state: ChatState, runtime: GraphRuntime
) -> dict[str, object]:
    """Persist user display name in state."""

    name = _clean_name((state.get("naming_intent") or {}).get("name"))
    if not name or state.get("user_name"):
        return {}
    companion_id = state.get("companion_id", "")
    store = runtime.resolve_companion_store()
    if store is not None and companion_id:
        await store.put_companion(
            companion_id,
            cast(CompanionRecord, {"user_name": name}),
        )
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
    store = runtime.resolve_companion_store()
    if store is None:
        return {
            "semantic_logs": [],
            "recent_logs": [],
            "emotions": [],
            "weather_info": weather_info,
        }

    companion_id = state.get("companion_id", "")
    if not companion_id:
        return {
            "semantic_logs": [],
            "recent_logs": [],
            "emotions": [],
            "weather_info": weather_info,
        }

    message = state.get("last_user_message", "")
    embedding = await runtime.resolve_embedding_provider().embed_text(message)
    semantic_logs = await store.search_chat(
        companion_id,
        query_embedding=embedding,
        limit=8,
    )
    recent_logs = await store.get_recent_chat(companion_id, limit=6)
    emotions = await store.get_emotions(companion_id, limit=3)
    return {
        "semantic_logs": semantic_logs,
        "recent_logs": recent_logs,
        "emotions": emotions,
        "weather_info": weather_info,
    }


async def compose_prompt(state: ChatState, runtime: GraphRuntime) -> dict[str, object]:
    """Compose a neutral public prompt."""

    return {
        "system_prompt": runtime.resolve_prompt_provider().build_chat_prompt(state)
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
    state: ChatState, runtime: GraphRuntime
) -> dict[str, object]:
    """Persist current user/AI turn when a companion store is configured."""

    store = runtime.resolve_companion_store()
    companion_id = state.get("companion_id", "")
    if store is None or not companion_id:
        return {}

    user_message = state.get("last_user_message", "")
    if user_message:
        user_embedding = await runtime.resolve_embedding_provider().embed_text(
            user_message
        )
        await store.add_chat_log(
            companion_id,
            sender="USER",
            message=user_message,
            embedding=user_embedding,
        )

    ai_text = state.get("pending_ai_text", "")
    if ai_text:
        ai_embedding = await runtime.resolve_embedding_provider().embed_text(ai_text)
        await store.add_chat_log(
            companion_id,
            sender="AI",
            message=ai_text,
            embedding=ai_embedding,
        )
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
        prompt = _NAMING_PROMPT_KO if _is_ko(state) else _NAMING_PROMPT
        return {
            "naming_phase": "awaiting_response",
            "naming_prompted": True,
            "emit": [event("naming_prompt", prompt)],
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
