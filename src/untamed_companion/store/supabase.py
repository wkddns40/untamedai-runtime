"""Optional Supabase companion store.

The Supabase SDK is imported lazily so core installs do not require
`supabase`. Install `untamedai-runtime[supabase]` before constructing this
adapter.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from importlib import import_module
from typing import Any, cast

from untamed_companion.exceptions import IntegrationNotConfiguredError
from untamed_companion.store.base import ChatLog, CompanionRecord, EmotionLog, Sender


@dataclass(slots=True)
class SupabaseCompanionStore:
    """Supabase adapter for the public companion store protocol."""

    url: str
    key: str
    companion_table: str = "Companions"
    chat_table: str = "Chat_Logs"
    emotion_table: str = "Daily_Emotions"
    _client: Any = field(init=False, repr=False)

    def __post_init__(self) -> None:
        try:
            supabase_module = import_module("supabase")
        except ImportError as exc:
            raise IntegrationNotConfiguredError(
                "SupabaseCompanionStore requires "
                "`pip install untamedai-runtime[supabase]`."
            ) from exc
        self._client = supabase_module.create_client(self.url, self.key)

    async def get_companion(self, companion_id: str) -> CompanionRecord | None:
        result = (
            self._client.table(self.companion_table)
            .select("*")
            .eq("companion_id", companion_id)
            .maybe_single()
            .execute()
        )
        return cast(CompanionRecord | None, result.data or None)

    async def put_companion(
        self,
        companion_id: str,
        values: CompanionRecord,
    ) -> CompanionRecord:
        row = dict(values)
        row["companion_id"] = companion_id
        result = (
            self._client.table(self.companion_table)
            .upsert(row)
            .execute()
        )
        data = result.data or [row]
        result_row = data[0] if isinstance(data, list) else data
        return cast(CompanionRecord, result_row)

    async def add_chat_log(
        self,
        companion_id: str,
        *,
        sender: Sender,
        message: str,
        embedding: list[float] | None = None,
    ) -> ChatLog:
        row: ChatLog = {
            "companion_id": companion_id,
            "sender": sender,
            "message": message,
        }
        if embedding is not None:
            row["embedding"] = embedding
        result = self._client.table(self.chat_table).insert(row).execute()
        data = result.data or [row]
        result_row = data[0] if isinstance(data, list) else data
        return cast(ChatLog, result_row)

    async def get_recent_chat(
        self,
        companion_id: str,
        *,
        limit: int = 6,
    ) -> list[ChatLog]:
        result = (
            self._client.table(self.chat_table)
            .select("*")
            .eq("companion_id", companion_id)
            .order("timestamp", desc=True)
            .limit(limit)
            .execute()
        )
        rows = list(result.data or [])
        rows.reverse()
        return rows

    async def search_chat(
        self,
        companion_id: str,
        *,
        query_embedding: list[float],
        limit: int = 8,
    ) -> list[ChatLog]:
        result = self._client.rpc(
            "match_chat_logs_v2",
            {
                "query_embedding": query_embedding,
                "target_companion_id": companion_id,
                "match_count": limit,
            },
        ).execute()
        return list(result.data or [])

    async def get_emotions(
        self,
        companion_id: str,
        *,
        limit: int = 3,
    ) -> list[EmotionLog]:
        result = (
            self._client.table(self.emotion_table)
            .select("*")
            .eq("companion_id", companion_id)
            .order("date", desc=True)
            .limit(limit)
            .execute()
        )
        return list(result.data or [])

    async def put_emotion(
        self,
        companion_id: str,
        *,
        date: str,
        values: EmotionLog,
    ) -> EmotionLog:
        row = dict(values)
        row["companion_id"] = companion_id
        row["date"] = date
        result = self._client.table(self.emotion_table).upsert(row).execute()
        data = result.data or [row]
        result_row = data[0] if isinstance(data, list) else data
        return cast(EmotionLog, result_row)
