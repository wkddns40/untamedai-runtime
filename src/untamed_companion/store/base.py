"""Store protocol for companion memory and profile data."""

from __future__ import annotations

from typing import Literal, Protocol, TypedDict

Sender = Literal["USER", "AI", "SYSTEM"]


class CompanionRecord(TypedDict, total=False):
    """Companion profile fields used by the public runtime."""

    companion_id: str
    user_id: str
    name: str
    user_name: str
    summary: str
    relationship_type: str
    tone_style: str


class ChatLog(TypedDict, total=False):
    """Chat log fields used by memory retrieval."""

    log_id: str
    companion_id: str
    sender: Sender
    message: str
    timestamp: str
    embedding: list[float]
    score: float


class EmotionLog(TypedDict, total=False):
    """Daily emotion fields used by prompt composition."""

    date: str
    companion_id: str
    primary_emotion: str
    color_hex: str
    summary_text: str
    key_quote: str


class CompanionStore(Protocol):
    """Async storage surface used by graph nodes.

    Implementations may back this with memory, Supabase, Postgres, or a
    consumer-owned service. Core graph tests use the in-memory implementation.
    """

    async def get_companion(self, companion_id: str) -> CompanionRecord | None:
        """Return companion profile, if present."""

    async def put_companion(
        self,
        companion_id: str,
        values: CompanionRecord,
    ) -> CompanionRecord:
        """Merge and return companion profile."""

    async def add_chat_log(
        self,
        companion_id: str,
        *,
        sender: Sender,
        message: str,
        embedding: list[float] | None = None,
    ) -> ChatLog:
        """Append one chat log."""

    async def get_recent_chat(
        self,
        companion_id: str,
        *,
        limit: int = 6,
    ) -> list[ChatLog]:
        """Return recent chat logs in chronological order."""

    async def search_chat(
        self,
        companion_id: str,
        *,
        query_embedding: list[float],
        limit: int = 8,
    ) -> list[ChatLog]:
        """Return semantically related chat logs."""

    async def get_emotions(
        self,
        companion_id: str,
        *,
        limit: int = 3,
    ) -> list[EmotionLog]:
        """Return recent daily emotions."""

    async def put_emotion(
        self,
        companion_id: str,
        *,
        date: str,
        values: EmotionLog,
    ) -> EmotionLog:
        """Upsert one daily emotion row."""

