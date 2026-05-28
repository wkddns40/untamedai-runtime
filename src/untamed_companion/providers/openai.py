"""Optional OpenAI-backed provider.

The OpenAI SDK is imported lazily so the core package has no OpenAI
dependency unless users install `untamedai-runtime[openai]`.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from importlib import import_module
from typing import TYPE_CHECKING, Any

from untamed_companion.exceptions import IntegrationNotConfiguredError

if TYPE_CHECKING:
    from untamed_companion.graph.state import ChatState, EmotionState


@dataclass(slots=True)
class OpenAIProvider:
    """OpenAI implementation of LLM and embedding provider protocols."""

    api_key: str | None = None
    chat_model: str = "gpt-4o-mini"
    embedding_model: str = "text-embedding-3-small"
    _client: Any = field(init=False, repr=False)

    def __post_init__(self) -> None:
        try:
            openai_module = import_module("openai")
        except ImportError as exc:
            raise IntegrationNotConfiguredError(
                "OpenAIProvider requires `pip install untamedai-runtime[openai]`."
            ) from exc
        self._client = openai_module.AsyncOpenAI(api_key=self.api_key)

    async def generate_chat_response(self, state: ChatState) -> str:
        prompt = state.get("system_prompt") or "You are a warm AI companion."
        message = state.get("last_user_message") or ""
        response = await self._client.chat.completions.create(
            model=self.chat_model,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": message},
            ],
            temperature=0.8,
        )
        return str(response.choices[0].message.content or "")

    async def generate_greeting(self, state: ChatState) -> str:
        companion = state.get("companion") or {}
        name = str(companion.get("name") or "Companion")
        response = await self._client.chat.completions.create(
            model=self.chat_model,
            messages=[
                {"role": "system", "content": "Write one short first greeting."},
                {"role": "user", "content": f"Companion name: {name}"},
            ],
            temperature=0.8,
        )
        return str(response.choices[0].message.content or "")

    async def analyze_emotion(self, state: EmotionState) -> dict[str, object]:
        logs = state.get("logs") or []
        response = await self._client.chat.completions.create(
            model=self.chat_model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Return JSON with primary_emotion, color_hex, "
                        "summary_text, key_quote."
                    ),
                },
                {"role": "user", "content": json.dumps(logs, ensure_ascii=False)},
            ],
            response_format={"type": "json_object"},
            temperature=0.0,
        )
        content = response.choices[0].message.content or "{}"
        data = json.loads(content)
        return data if isinstance(data, dict) else {}

    async def embed_text(self, text: str) -> list[float]:
        response = await self._client.embeddings.create(
            model=self.embedding_model,
            input=text,
        )
        return list(response.data[0].embedding)
