"""Neutral default prompts for the public runtime."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from untamed_companion.graph.state import ChatState, EmotionState


def _safe_text(value: object, fallback: str = "") -> str:
    text = str(value or "").strip()
    return text or fallback


def _companion_name(state: ChatState) -> str:
    companion = state.get("companion") or {}
    return _safe_text(companion.get("name"), "Companion")


def _user_name(state: ChatState) -> str:
    return _safe_text(state.get("user_name"), "friend")


def _format_rows(rows: Sequence[Mapping[str, object]], *, limit: int) -> str:
    formatted: list[str] = []
    for row in rows[:limit]:
        sender = _safe_text(row.get("sender"), "UNKNOWN")
        message = _safe_text(row.get("message"))
        if message:
            formatted.append(f"- {sender}: {message}")
    return "\n".join(formatted)


@dataclass(frozen=True, slots=True)
class DefaultPromptProvider:
    """Public-safe neutral prompt templates."""

    def build_chat_prompt(self, state: ChatState) -> str:
        name = _companion_name(state)
        user_name = _user_name(state)
        lang = _safe_text(state.get("user_lang"), "en")
        lines = [
            f"You are {name}, a conversational AI companion.",
            f"Speak with {user_name} in a warm, concise, grounded way.",
            f"Use language code: {lang}.",
            "Do not claim hidden abilities, private data, or real-world actions.",
            "Use supplied memory and context only when it is relevant.",
        ]
        weather = _safe_text(state.get("weather_info"))
        if weather:
            lines.append(f"Context weather: {weather}")
        emotions = state.get("emotions") or []
        if emotions:
            latest = emotions[0]
            summary = _safe_text(latest.get("summary_text"))
            primary = _safe_text(latest.get("primary_emotion"))
            if primary or summary:
                lines.append(f"Recent emotional context: {primary} {summary}".strip())
        recent_logs = _format_rows(state.get("recent_logs") or [], limit=6)
        if recent_logs:
            lines.append("Recent conversation:\n" + recent_logs)
        semantic_logs = _format_rows(state.get("semantic_logs") or [], limit=4)
        if semantic_logs:
            lines.append("Related memories:\n" + semantic_logs)
        return "\n".join(lines)

    def build_greeting_prompt(self, state: ChatState) -> str:
        name = _companion_name(state)
        lang = _safe_text(state.get("user_lang"), "en")
        return "\n".join(
            [
                f"You are {name}, a conversational AI companion.",
                "Write one short first greeting.",
                f"Use language code: {lang}.",
                "Keep the greeting neutral, welcoming, and product-agnostic.",
            ]
        )

    def build_emotion_prompt(self, _state: EmotionState) -> str:
        return "\n".join(
            [
                "Analyze one day of conversation logs.",
                "Return a JSON object with primary_emotion, color_hex, "
                "summary_text, and key_quote.",
                "Keep the analysis neutral, compact, and free of product copy.",
            ]
        )


@dataclass(frozen=True, slots=True)
class StaticPromptProvider:
    """Prompt provider for simple overrides in tests and small apps."""

    chat_prompt: str | None = None
    greeting_prompt: str | None = None
    emotion_prompt: str | None = None
    fallback: DefaultPromptProvider = field(default_factory=DefaultPromptProvider)

    def build_chat_prompt(self, state: ChatState) -> str:
        return self.chat_prompt or self.fallback.build_chat_prompt(state)

    def build_greeting_prompt(self, state: ChatState) -> str:
        return self.greeting_prompt or self.fallback.build_greeting_prompt(state)

    def build_emotion_prompt(self, state: EmotionState) -> str:
        return self.emotion_prompt or self.fallback.build_emotion_prompt(state)
