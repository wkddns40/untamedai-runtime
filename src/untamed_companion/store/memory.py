"""In-memory companion store for tests and demos."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from datetime import UTC, datetime
from math import sqrt
from typing import cast
from uuid import uuid4

from untamed_companion.store.base import ChatLog, CompanionRecord, EmotionLog, Sender


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _cosine(left: list[float], right: list[float]) -> float:
    if not left or not right:
        return 0.0
    size = min(len(left), len(right))
    dot = sum(left[i] * right[i] for i in range(size))
    left_norm = sqrt(sum(value * value for value in left[:size]))
    right_norm = sqrt(sum(value * value for value in right[:size]))
    if left_norm == 0.0 or right_norm == 0.0:
        return 0.0
    return dot / (left_norm * right_norm)


@dataclass(slots=True)
class InMemoryCompanionStore:
    """Process-local store with copy-on-read/write semantics."""

    companions: dict[str, CompanionRecord] = field(default_factory=dict)
    chat_logs: dict[str, list[ChatLog]] = field(default_factory=dict)
    emotions: dict[str, dict[str, EmotionLog]] = field(default_factory=dict)

    async def get_companion(self, companion_id: str) -> CompanionRecord | None:
        record = self.companions.get(companion_id)
        return deepcopy(record) if record is not None else None

    async def put_companion(
        self,
        companion_id: str,
        values: CompanionRecord,
    ) -> CompanionRecord:
        current = dict(self.companions.get(companion_id, {}))
        current.update(values)
        current["companion_id"] = companion_id
        record = cast(CompanionRecord, current)
        self.companions[companion_id] = record
        return deepcopy(record)

    async def add_chat_log(
        self,
        companion_id: str,
        *,
        sender: Sender,
        message: str,
        embedding: list[float] | None = None,
    ) -> ChatLog:
        row: ChatLog = {
            "log_id": str(uuid4()),
            "companion_id": companion_id,
            "sender": sender,
            "message": message,
            "timestamp": _now_iso(),
        }
        if embedding is not None:
            row["embedding"] = list(embedding)
        self.chat_logs.setdefault(companion_id, []).append(row)
        return deepcopy(row)

    async def get_recent_chat(
        self,
        companion_id: str,
        *,
        limit: int = 6,
    ) -> list[ChatLog]:
        rows = self.chat_logs.get(companion_id, [])[-limit:]
        return deepcopy(rows)

    async def search_chat(
        self,
        companion_id: str,
        *,
        query_embedding: list[float],
        limit: int = 8,
    ) -> list[ChatLog]:
        scored: list[ChatLog] = []
        for row in self.chat_logs.get(companion_id, []):
            embedding = row.get("embedding") or []
            score = _cosine(query_embedding, embedding)
            if score <= 0.0:
                continue
            scored_row = deepcopy(row)
            scored_row["score"] = score
            scored.append(scored_row)
        scored.sort(key=lambda row: row.get("score", 0.0), reverse=True)
        return scored[:limit]

    async def get_emotions(
        self,
        companion_id: str,
        *,
        limit: int = 3,
    ) -> list[EmotionLog]:
        rows = sorted(
            self.emotions.get(companion_id, {}).values(),
            key=lambda row: row.get("date", ""),
            reverse=True,
        )
        return deepcopy(rows[:limit])

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
        emotion = cast(EmotionLog, row)
        self.emotions.setdefault(companion_id, {})[date] = emotion
        return deepcopy(emotion)
