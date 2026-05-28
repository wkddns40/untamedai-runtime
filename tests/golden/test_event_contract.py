from __future__ import annotations

import json
from pathlib import Path

import pytest
from tests.golden._diff import diff_events

from untamed_companion.graph import build_chat_graph

FIXTURES_DIR = Path(__file__).with_name("fixtures")


def _load_fixture(name: str) -> list[dict[str, object]]:
    raw = (FIXTURES_DIR / f"{name}.json").read_text(encoding="utf-8")
    loaded = json.loads(raw)
    if not isinstance(loaded, list):
        raise TypeError(f"Fixture {name} must contain a JSON array.")
    return [dict(event) for event in loaded]


def _assert_events_match(
    actual: list[dict[str, object]],
    fixture_name: str,
) -> None:
    expected = _load_fixture(fixture_name)
    diff = diff_events(actual, expected)
    assert not diff, "\n".join(diff)


async def _chat_events(state: dict[str, object]) -> list[dict[str, object]]:
    graph = build_chat_graph()
    result = await graph.ainvoke(state)
    raw_events = result["emit"]
    return [dict(event) for event in raw_events]


@pytest.mark.parametrize(
    ("fixture_name", "state"),
    [
        (
            "chat_basic_en",
            {
                "companion_id": "demo",
                "last_user_message": "hello",
                "user_name": "Min",
                "user_lang": "en",
                "companion": {"name": "Luna"},
            },
        ),
        (
            "ai_naming_en",
            {
                "companion_id": "demo",
                "last_user_message": "your name is Luna",
                "user_lang": "en",
                "companion": {"name": "???"},
            },
        ),
        (
            "ai_naming_ko",
            {
                "companion_id": "demo",
                "last_user_message": "네 이름은 루나",
                "user_lang": "ko",
                "companion": {"name": "???"},
            },
        ),
        (
            "user_intro_en",
            {
                "companion_id": "demo",
                "last_user_message": "my name is Min",
                "user_lang": "en",
                "companion": {"name": "Luna"},
            },
        ),
        (
            "user_intro_ko",
            {
                "companion_id": "demo",
                "last_user_message": "내 이름은 민",
                "user_lang": "ko",
                "companion": {"name": "루나"},
            },
        ),
        (
            "coffee_en",
            {
                "companion_id": "demo",
                "last_user_message": "coffee",
                "msg_type": "coffee_turn",
                "user_lang": "en",
            },
        ),
        (
            "coffee_ko",
            {
                "companion_id": "demo",
                "last_user_message": "커피",
                "msg_type": "coffee_turn",
                "user_lang": "ko",
            },
        ),
    ],
)
async def test_chat_event_contract(
    fixture_name: str,
    state: dict[str, object],
) -> None:
    _assert_events_match(await _chat_events(state), fixture_name)
