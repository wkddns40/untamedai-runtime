"""Readable event diff helpers for golden contract tests."""

from __future__ import annotations

import difflib
import json
from typing import Any


def merge_stream_chunks(events: list[dict[str, object]]) -> list[dict[str, object]]:
    """Coalesce adjacent stream chunks into one event."""

    merged: list[dict[str, object]] = []
    for event in events:
        if (
            event.get("type") == "stream"
            and merged
            and merged[-1].get("type") == "stream"
        ):
            previous = merged[-1]
            previous["content"] = str(previous.get("content") or "") + str(
                event.get("content") or ""
            )
        else:
            merged.append(dict(event))
    return merged


def _normalize_value(value: Any) -> Any:
    if isinstance(value, str):
        return " ".join(value.split())
    return value


def normalize_events(events: list[dict[str, object]]) -> list[dict[str, object]]:
    """Normalize whitespace and stream chunking."""

    normalized: list[dict[str, object]] = []
    for event in merge_stream_chunks(events):
        copy = dict(event)
        if "content" in copy:
            copy["content"] = _normalize_value(copy["content"])
        normalized.append(copy)
    return normalized


def diff_events(
    actual: list[dict[str, object]],
    expected: list[dict[str, object]],
) -> list[str]:
    """Return unified diff lines, or [] when contract-equivalent."""

    normalized_actual = normalize_events(actual)
    normalized_expected = normalize_events(expected)
    if normalized_actual == normalized_expected:
        return []

    def _format(events: list[dict[str, object]]) -> list[str]:
        return [
            json.dumps(event, ensure_ascii=False, sort_keys=True)
            for event in events
        ]

    return list(
        difflib.unified_diff(
            _format(normalized_expected),
            _format(normalized_actual),
            fromfile="expected",
            tofile="actual",
            lineterm="",
        )
    )
