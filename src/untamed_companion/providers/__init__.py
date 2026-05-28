"""Provider interfaces and default fake implementations."""

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
from untamed_companion.providers.openai import OpenAIProvider
from untamed_companion.providers.weather import StaticWeatherProvider

__all__ = [
    "ChatResponder",
    "EmbeddingProvider",
    "EmotionAnalyzer",
    "FakeEmbeddingProvider",
    "FakeLLMProvider",
    "FakeWeatherProvider",
    "GreetingResponder",
    "LLMProvider",
    "OpenAIProvider",
    "StaticWeatherProvider",
    "WeatherProvider",
]
