"""Provider protocols used by runtime graphs."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from untamed_companion.graph.state import ChatState, EmotionState


class ChatResponder(Protocol):
    """Generate one assistant response for a chat turn."""

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


class LLMProvider(ChatResponder, GreetingResponder, EmotionAnalyzer, Protocol):
    """Combined LLM provider surface for the public runtime."""


class EmbeddingProvider(Protocol):
    """Generate embedding vectors."""

    async def embed_text(self, text: str) -> list[float]:
        """Return an embedding vector for text."""


class WeatherProvider(Protocol):
    """Fetch external weather/context information."""

    async def get_weather(self, *, location: str, lang: str = "en") -> str:
        """Return a natural-language weather summary."""
