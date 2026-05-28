from untamed_companion.graph import GraphRuntime, build_chat_graph
from untamed_companion.providers import FakeEmbeddingProvider, FakeWeatherProvider
from untamed_companion.store import InMemoryCompanionStore, SupabaseCompanionStore


async def test_in_memory_store_roundtrip() -> None:
    store = InMemoryCompanionStore()
    await store.put_companion("cid", {"name": "Luna"})
    await store.add_chat_log(
        "cid",
        sender="USER",
        message="hello",
        embedding=[1.0, 0.0],
    )
    await store.put_emotion(
        "cid",
        date="2026-05-28",
        values={
            "primary_emotion": "calm",
            "color_hex": "#8ecae6",
            "summary_text": "quiet",
        },
    )

    companion = await store.get_companion("cid")
    recent = await store.get_recent_chat("cid")
    semantic = await store.search_chat("cid", query_embedding=[1.0, 0.0])
    emotions = await store.get_emotions("cid")

    assert companion and companion["name"] == "Luna"
    assert recent[0]["message"] == "hello"
    assert semantic[0]["score"] == 1.0
    assert emotions[0]["primary_emotion"] == "calm"


async def test_chat_graph_loads_and_persists_with_store() -> None:
    store = InMemoryCompanionStore()
    await store.put_companion("cid", {"name": "Luna", "user_name": "Min"})
    runtime = GraphRuntime(
        companion_store=store,
        embedding_provider=FakeEmbeddingProvider(dimensions=4),
        weather_provider=FakeWeatherProvider("Clear"),
    )
    graph = build_chat_graph(runtime=runtime)

    result = await graph.ainvoke(
        {
            "companion_id": "cid",
            "last_user_message": "hello",
        }
    )

    recent = await store.get_recent_chat("cid", limit=10)
    assert result["companion"]["name"] == "Luna"
    assert result["user_name"] == "Min"
    assert result["weather_info"] == "Clear"
    assert [row["sender"] for row in recent] == ["USER", "AI"]


async def test_chat_graph_updates_names_in_store() -> None:
    store = InMemoryCompanionStore()
    runtime = GraphRuntime(companion_store=store)
    graph = build_chat_graph(runtime=runtime)

    await graph.ainvoke(
        {
            "companion_id": "cid",
            "last_user_message": "your name is Luna",
            "companion": {"name": "???"},
        }
    )

    companion = await store.get_companion("cid")
    assert companion and companion["name"] == "Luna"


def test_supabase_store_imports_without_supabase_dependency() -> None:
    assert SupabaseCompanionStore.__name__ == "SupabaseCompanionStore"
