"""Provider and prompt override example for consumer applications."""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from typing import TYPE_CHECKING

from untamed_companion.graph import GraphRuntime, build_chat_graph
from untamed_companion.prompts import PromptProvider
from untamed_companion.store import InMemoryCompanionStore

if TYPE_CHECKING:
    from untamed_companion.graph.state import ChatState, EmotionState


@dataclass(slots=True)
class ExampleProvider:
    """Single object implementing the demo provider protocols."""

    label: str = "Override demo"

    async def generate_chat_response(self, state: ChatState) -> str:
        message = state.get("last_user_message") or ""
        return f"{self.label}: handled '{message}' with app-owned policy."

    async def generate_greeting(self, state: ChatState) -> str:
        companion = state.get("companion") or {}
        name = companion.get("name") or "Companion"
        return f"{name}: hello from the override provider."

    async def analyze_emotion(self, state: EmotionState) -> dict[str, object]:
        logs = state.get("logs") or []
        return {
            "primary_emotion": "steady",
            "color_hex": "#6b7280",
            "summary_text": f"Override provider reviewed {len(logs)} logs.",
            "key_quote": "",
        }

    async def embed_text(self, text: str) -> list[float]:
        length = max(len(text), 1)
        return [min(length / 100.0, 1.0), 1.0]

    async def get_weather(self, *, location: str, lang: str = "en") -> str:
        return f"{location}: static override weather ({lang})."


@dataclass(slots=True)
class ExamplePromptProvider(PromptProvider):
    """App-owned prompt provider used by the example runtime."""

    policy_name: str = "consumer-policy"

    def build_chat_prompt(self, state: ChatState) -> str:
        lang = state.get("user_lang") or "en"
        return f"{self.policy_name}: answer in {lang}; keep responses compact."

    def build_greeting_prompt(self, state: ChatState) -> str:
        lang = state.get("user_lang") or "en"
        return f"{self.policy_name}: greet once in {lang}."

    def build_emotion_prompt(self, _state: EmotionState) -> str:
        return f"{self.policy_name}: summarize daily emotion as JSON."


async def run_turn() -> dict[str, object]:
    provider = ExampleProvider()
    runtime = GraphRuntime(
        llm_provider=provider,
        embedding_provider=provider,
        weather_provider=provider,
        prompt_provider=ExamplePromptProvider(),
        companion_store=InMemoryCompanionStore(),
    )
    graph = build_chat_graph(runtime=runtime)
    result = await graph.ainvoke(
        {
            "companion_id": "demo",
            "last_user_message": "hello from my app",
            "user_lang": "en",
            "companion": {"name": "Luna"},
        }
    )
    return dict(result)


async def main() -> None:
    result = await run_turn()
    print(json.dumps(result["emit"], ensure_ascii=False, indent=2))
    print(result["system_prompt"])


if __name__ == "__main__":
    asyncio.run(main())
