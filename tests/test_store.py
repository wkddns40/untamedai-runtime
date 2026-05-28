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


class _SupabaseResult:
    def __init__(self, data: object) -> None:
        self.data = data


class _SupabaseQuery:
    def __init__(self, client: "_SupabaseClient", table: str) -> None:
        self.client = client
        self.table = table
        self.operation = "select"
        self.payload: dict[str, object] | None = None

    def select(self, columns: str) -> "_SupabaseQuery":
        self.client.calls.append(("select", self.table, columns))
        return self

    def eq(self, column: str, value: object) -> "_SupabaseQuery":
        self.client.calls.append(("eq", self.table, column, value))
        return self

    def maybe_single(self) -> "_SupabaseQuery":
        self.client.calls.append(("maybe_single", self.table))
        self.operation = "companion"
        return self

    def upsert(self, payload: dict[str, object]) -> "_SupabaseQuery":
        self.client.calls.append(("upsert", self.table, payload))
        self.operation = "write"
        self.payload = payload
        return self

    def insert(self, payload: dict[str, object]) -> "_SupabaseQuery":
        self.client.calls.append(("insert", self.table, payload))
        self.operation = "write"
        self.payload = payload
        return self

    def order(self, column: str, *, desc: bool) -> "_SupabaseQuery":
        self.client.calls.append(("order", self.table, column, desc))
        return self

    def limit(self, value: int) -> "_SupabaseQuery":
        self.client.calls.append(("limit", self.table, value))
        return self

    def execute(self) -> _SupabaseResult:
        if self.operation == "companion":
            return _SupabaseResult({"companion_id": "cid", "name": "Luna"})
        if self.operation == "write":
            return _SupabaseResult([self.payload])
        if self.table == "chats":
            return _SupabaseResult(
                [
                    {"message": "newest"},
                    {"message": "oldest"},
                ]
            )
        return _SupabaseResult([{"primary_emotion": "calm"}])


class _SupabaseRpc:
    def __init__(self, client: "_SupabaseClient", name: str, params: object) -> None:
        self.client = client
        self.name = name
        self.params = params

    def execute(self) -> _SupabaseResult:
        self.client.calls.append(("execute_rpc", self.name, self.params))
        return _SupabaseResult([{"message": "semantic", "score": 0.5}])


class _SupabaseClient:
    def __init__(self) -> None:
        self.calls: list[tuple[object, ...]] = []

    def table(self, name: str) -> _SupabaseQuery:
        self.calls.append(("table", name))
        return _SupabaseQuery(self, name)

    def rpc(self, name: str, params: object) -> _SupabaseRpc:
        self.calls.append(("rpc", name, params))
        return _SupabaseRpc(self, name, params)


async def test_supabase_store_uses_injected_client_and_custom_names() -> None:
    client = _SupabaseClient()
    store = SupabaseCompanionStore(
        url="",
        key="",
        companion_table="companions",
        chat_table="chats",
        emotion_table="emotions",
        match_chat_rpc="match_chat",
        client=client,
    )

    companion = await store.get_companion("cid")
    saved = await store.put_companion("cid", {"name": "Luna"})
    chat = await store.add_chat_log("cid", sender="USER", message="hello")
    recent = await store.get_recent_chat("cid")
    semantic = await store.search_chat("cid", query_embedding=[1.0], limit=2)
    emotion = await store.put_emotion(
        "cid",
        date="2026-05-28",
        values={"primary_emotion": "calm"},
    )

    assert companion and companion["name"] == "Luna"
    assert saved["companion_id"] == "cid"
    assert chat["message"] == "hello"
    assert [row["message"] for row in recent] == ["oldest", "newest"]
    assert semantic[0]["score"] == 0.5
    assert emotion["date"] == "2026-05-28"
    assert ("table", "companions") in client.calls
    assert ("table", "chats") in client.calls
    assert ("table", "emotions") in client.calls
    assert any(call[0] == "rpc" and call[1] == "match_chat" for call in client.calls)
