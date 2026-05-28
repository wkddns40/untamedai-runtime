"""Runtime hooks used by public graph nodes."""

from __future__ import annotations

from dataclasses import dataclass

from untamed_companion.providers.base import (
    ChatResponder,
    EmbeddingProvider,
    EmotionAnalyzer,
    GreetingResponder,
    LLMProvider,
    WeatherProvider,
)
from untamed_companion.providers.fake import (
    FakeEmbeddingProvider,
    FakeLLMProvider,
    FakeWeatherProvider,
)


@dataclass(slots=True)
class GraphRuntime:
    """Injectable runtime dependencies for graph builders."""

    llm_provider: LLMProvider | None = None
    chat_responder: ChatResponder | None = None
    greeting_responder: GreetingResponder | None = None
    emotion_analyzer: EmotionAnalyzer | None = None
    embedding_provider: EmbeddingProvider | None = None
    weather_provider: WeatherProvider | None = None

    def resolve_chat_responder(self) -> ChatResponder:
        return self.chat_responder or self.llm_provider or FakeLLMProvider()

    def resolve_greeting_responder(self) -> GreetingResponder:
        return self.greeting_responder or self.llm_provider or FakeLLMProvider()

    def resolve_emotion_analyzer(self) -> EmotionAnalyzer:
        return self.emotion_analyzer or self.llm_provider or FakeLLMProvider()

    def resolve_embedding_provider(self) -> EmbeddingProvider:
        return self.embedding_provider or FakeEmbeddingProvider()

    def resolve_weather_provider(self) -> WeatherProvider:
        return self.weather_provider or FakeWeatherProvider()
