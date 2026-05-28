from untamed_companion import __version__
from untamed_companion.graph import (
    GraphRuntime,
    build_chat_graph,
    build_emotion_graph,
    build_greeting_graph,
)
from untamed_companion.providers import (
    FakeEmbeddingProvider,
    FakeLLMProvider,
    FakeWeatherProvider,
    OpenAIProvider,
)


def test_package_imports() -> None:
    assert __version__ == "1.0.0"


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


async def test_chat_graph_uses_llm_provider() -> None:
    graph = build_chat_graph(
        runtime=GraphRuntime(llm_provider=FakeLLMProvider(chat_text="custom"))
    )
    result = await graph.ainvoke(
        {
            "companion_id": "demo",
            "last_user_message": "hello",
            "companion": {"name": "Luna"},
        }
    )

    assert result["emit"][0]["content"] == "custom"


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


async def test_chat_graph_detects_korean_naming_events() -> None:
    graph = build_chat_graph(runtime=GraphRuntime())
    result = await graph.ainvoke(
        {
            "companion_id": "demo",
            "last_user_message": "네 이름은 루나",
            "user_lang": "ko",
            "companion": {"name": "???"},
        }
    )

    assert [event["type"] for event in result["emit"]] == [
        "name_reveal",
        "stream",
        "end",
    ]
    assert result["companion"]["name"] == "루나"
    assert result["emit"][1]["content"] == "저를 루나라고 불러 주세요."


async def test_chat_graph_detects_korean_user_name() -> None:
    graph = build_chat_graph(runtime=GraphRuntime())
    result = await graph.ainvoke(
        {
            "companion_id": "demo",
            "last_user_message": "내 이름은 민",
            "user_lang": "ko",
            "companion": {"name": "루나"},
        }
    )

    assert result["user_name"] == "민"
    assert result["emit"][0] == {"type": "user_name_set", "content": "민"}


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


async def test_chat_graph_emits_korean_coffee_request() -> None:
    graph = build_chat_graph()
    result = await graph.ainvoke(
        {
            "companion_id": "demo",
            "last_user_message": "커피",
            "msg_type": "coffee_turn",
            "user_lang": "ko",
        }
    )

    assert result["emit"] == [
        {"type": "coffee_request", "content": "따뜻한 커피 한 잔이 필요해요."}
    ]


async def test_chat_graph_uses_weather_provider() -> None:
    graph = build_chat_graph(
        runtime=GraphRuntime(weather_provider=FakeWeatherProvider("Clear, 21C"))
    )
    result = await graph.ainvoke(
        {
            "companion_id": "demo",
            "last_user_message": "hello",
            "companion": {"name": "Luna"},
        }
    )

    assert result["weather_info"] == "Clear, 21C"


async def test_greeting_graph_emits_greeting() -> None:
    graph = build_greeting_graph()
    result = await graph.ainvoke({"companion": {"name": "Luna"}})

    assert result["emit"][0]["type"] == "greeting"


async def test_fake_llm_provider_uses_korean_language() -> None:
    graph = build_chat_graph()
    result = await graph.ainvoke(
        {
            "companion_id": "demo",
            "last_user_message": "안녕",
            "user_name": "민",
            "user_lang": "ko",
            "companion": {"name": "루나"},
        }
    )

    assert result["emit"][0]["content"] == "루나: 들었어요, 민. 이렇게 말했어요: 안녕"


async def test_fake_embedding_provider_is_deterministic() -> None:
    provider = FakeEmbeddingProvider(dimensions=4)
    first = await provider.embed_text("hello")
    second = await provider.embed_text("hello")

    assert first == second
    assert len(first) == 4


async def test_emotion_graph_skips_empty_logs() -> None:
    graph = build_emotion_graph()
    result = await graph.ainvoke({"companion_id": "demo", "logs": []})

    assert result["skipped"] is True


def test_openai_provider_imports_without_openai_dependency() -> None:
    assert OpenAIProvider.__name__ == "OpenAIProvider"
