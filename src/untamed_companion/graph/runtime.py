"""Runtime hooks used by public graph nodes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from untamed_companion.graph.state import ChatState, EmotionState


class ChatResponder(Protocol):
    """Generate one assistant response for the current state."""

    async def generate_chat_response(self, state: ChatState) -> str:
        """Return assistant text."""


class GreetingResponder(Protocol):
    """Generate the first greeting."""

    async def generate_greeting(self, state: ChatState) -> str:
        """Return greeting text."""


class EmotionAnalyzer(Protocol):
    """Analyze one day of conversation logs."""

    async def analyze_emotion(self, state: EmotionState) -> dict[str, object]:
        """Return daily emotion analysis."""


class DefaultResponder:
    """Deterministic fallback responder for tests and demos."""

    async def generate_chat_response(self, state: ChatState) -> str:
        companion = state.get("companion") or {}
        name = str(companion.get("name") or "Companion")
        user_name = state.get("user_name") or "friend"
        message = state.get("last_user_message") or ""
        return f"{name}: I heard you, {user_name}. You said: {message}"

    async def generate_greeting(self, state: ChatState) -> str:
        companion = state.get("companion") or {}
        name = str(companion.get("name") or "Companion")
        return f"{name}: Hello. I am here with you."


class DefaultEmotionAnalyzer:
    """Simple deterministic emotion analyzer."""

    async def analyze_emotion(self, state: EmotionState) -> dict[str, object]:
        logs = state.get("logs") or []
        if not logs:
            return {}
        return {
            "primary_emotion": "calm",
            "color_hex": "#8ecae6",
            "summary_text": f"Processed {len(logs)} messages.",
            "key_quote": "",
        }


@dataclass(slots=True)
class GraphRuntime:
    """Injectable runtime dependencies for graph builders."""

    chat_responder: ChatResponder | None = None
    greeting_responder: GreetingResponder | None = None
    emotion_analyzer: EmotionAnalyzer | None = None

    def resolve_chat_responder(self) -> ChatResponder:
        return self.chat_responder or DefaultResponder()

    def resolve_greeting_responder(self) -> GreetingResponder:
        return self.greeting_responder or DefaultResponder()

    def resolve_emotion_analyzer(self) -> EmotionAnalyzer:
        return self.emotion_analyzer or DefaultEmotionAnalyzer()

