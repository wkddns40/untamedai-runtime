"""Weather provider implementations."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class StaticWeatherProvider:
    """Simple static weather provider for demos."""

    text: str = ""

    async def get_weather(self, *, location: str, lang: str = "en") -> str:
        if self.text:
            return self.text
        if lang == "ko":
            return f"{location} 날씨 정보 없음"
        return f"No weather data for {location}."
