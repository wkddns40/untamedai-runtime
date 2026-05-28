from untamed_companion import __version__
from untamed_companion.graph import (
    GraphRuntime,
    build_chat_graph,
    build_emotion_graph,
    build_greeting_graph,
)


def test_package_imports() -> None:
    assert __version__ == "0.0.0"


async def test_chat_graph_emits_chat_response() -> None:
    graph = build_chat_graph()
    result = await graph.ainvoke(
        {
            "companion_id": "demo",
            "last_user_message": "hello",
            "user_name": "Min",
            "companion": {"name": "Luna"},
        }
    )

    assert [event["type"] for event in result["emit"]] == ["stream", "end"]
    assert result["emit"][-1]["intent"] == "chat"


async def test_chat_graph_emits_naming_events() -> None:
    graph = build_chat_graph(runtime=GraphRuntime())
    result = await graph.ainvoke(
        {
            "companion_id": "demo",
            "last_user_message": "your name is Luna",
            "companion": {"name": "???"},
        }
    )

    assert [event["type"] for event in result["emit"]] == [
        "name_reveal",
        "stream",
        "end",
    ]
    assert result["companion"]["name"] == "Luna"


async def test_chat_graph_emits_coffee_request() -> None:
    graph = build_chat_graph()
    result = await graph.ainvoke(
        {
            "companion_id": "demo",
            "last_user_message": "coffee",
            "msg_type": "coffee_turn",
        }
    )

    assert [event["type"] for event in result["emit"]] == ["coffee_request"]


async def test_greeting_graph_emits_greeting() -> None:
    graph = build_greeting_graph()
    result = await graph.ainvoke({"companion": {"name": "Luna"}})

    assert result["emit"][0]["type"] == "greeting"


async def test_emotion_graph_skips_empty_logs() -> None:
    graph = build_emotion_graph()
    result = await graph.ainvoke({"companion_id": "demo", "logs": []})

    assert result["skipped"] is True
