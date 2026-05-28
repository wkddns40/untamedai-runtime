"""Deterministic fake providers for tests and demos."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from untamed_companion.graph.state import ChatState, EmotionState


@dataclass(slots=True)
class FakeLLMProvider:
    """Deterministic LLM provider."""

    chat_text: str | None = None
    greeting_text: str | None = None
    emotion_analysis: dict[str, object] = field(default_factory=dict)

    async def generate_chat_response(self, state: ChatState) -> str:
        if self.chat_text is not None:
            return self.chat_text
        companion = state.get("companion") or {}
        name = str(companion.get("name") or "Companion")
        user_name = state.get("user_name") or "friend"
        message = state.get("last_user_message") or ""
        return f"{name}: I heard you, {user_name}. You said: {message}"

    async def generate_greeting(self, state: ChatState) -> str:
        if self.greeting_text is not None:
            return self.greeting_text
        companion = state.get("companion") or {}
        name = str(companion.get("name") or "Companion")
        return f"{name}: Hello. I am here with you."

    async def analyze_emotion(self, state: EmotionState) -> dict[str, object]:
        if self.emotion_analysis:
            return dict(self.emotion_analysis)
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
class FakeEmbeddingProvider:
    """Small deterministic embedding provider."""

    dimensions: int = 8

    async def embed_text(self, text: str) -> list[float]:
        if self.dimensions <= 0:
            return []
        buckets = [0.0 for _ in range(self.dimensions)]
        for index, char in enumerate(text.encode("utf-8")):
            buckets[index % self.dimensions] += float(char)
        norm = max(sum(abs(value) for value in buckets), 1.0)
        return [value / norm for value in buckets]


@dataclass(slots=True)
class FakeWeatherProvider:
    """Static weather provider."""

    text: str = ""

    async def get_weather(self, *, location: str, lang: str = "en") -> str:
        if self.text:
            return self.text
        if lang == "ko":
            return f"{location} 날씨 정보 없음"
        return f"No weather data for {location}."
