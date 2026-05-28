# Persistence

`untamedai-runtime` keeps persistence optional. Core installs do not include
Supabase, Postgres, or database drivers.

## Install Extras

Supabase store adapter:

```bash
pip install "untamedai-runtime[supabase]"
```

Postgres checkpointer helper:

```bash
pip install "untamedai-runtime[postgres]"
```

## Companion Store

The runtime depends on the `CompanionStore` protocol, not a specific database
schema. Implementations must provide these async methods:

- `get_companion`
- `put_companion`
- `add_chat_log`
- `get_recent_chat`
- `search_chat`
- `get_emotions`
- `put_emotion`

Logical row shapes are documented by `CompanionRecord`, `ChatLog`, and
`EmotionLog` in `untamed_companion.store`.

## Supabase Adapter

`SupabaseCompanionStore` imports the Supabase SDK only when an instance is
created without an injected client.

```python
from untamed_companion.store import SupabaseCompanionStore

store = SupabaseCompanionStore(
    url="https://your-project.supabase.co",
    key="your-publishable-or-service-key",
)
```

Default table/RPC names:

| Setting | Default |
| --- | --- |
| `companion_table` | `Companions` |
| `chat_table` | `Chat_Logs` |
| `emotion_table` | `Daily_Emotions` |
| `match_chat_rpc` | `match_chat_logs_v2` |
| `companion_id_column` | `companion_id` |
| `chat_order_column` | `timestamp` |
| `emotion_order_column` | `date` |

Override names when your application schema differs:

```python
store = SupabaseCompanionStore(
    url="https://your-project.supabase.co",
    key="your-key",
    companion_table="companions",
    chat_table="chat_logs",
    emotion_table="daily_emotions",
    match_chat_rpc="match_companion_chat",
)
```

For tests, inject a Supabase-like client and avoid the optional dependency:

```python
store = SupabaseCompanionStore(url="", key="", client=fake_supabase_client)
```

## Suggested Supabase Shape

These snippets are illustrative only. Keep production RLS, indexes, and tenant
policy in your application migrations.

```sql
create table companions (
  companion_id text primary key,
  user_id text,
  name text,
  user_name text,
  summary text,
  relationship_type text,
  tone_style text
);

create table chat_logs (
  log_id uuid primary key default gen_random_uuid(),
  companion_id text not null,
  sender text not null,
  message text not null,
  timestamp timestamptz not null default now(),
  embedding vector
);

create table daily_emotions (
  companion_id text not null,
  date date not null,
  primary_emotion text,
  color_hex text,
  summary_text text,
  key_quote text,
  primary key (companion_id, date)
);
```

Semantic search is app-owned. The adapter calls `match_chat_rpc` with:

```json
{
  "query_embedding": [0.1, 0.2],
  "target_companion_id": "demo",
  "match_count": 8
}
```

## Postgres Checkpointer

Use `create_async_postgres_checkpointer(...)` for LangGraph checkpoint state.
This is separate from `CompanionStore`, which stores companion profile, chat,
and emotion records.

```python
from untamed_companion.checkpoint import create_async_postgres_checkpointer
from untamed_companion.graph import GraphRuntime, build_chat_graph

async with create_async_postgres_checkpointer(
    "postgresql://user:pass@localhost:5432/app",
) as checkpointer:
    graph = build_chat_graph(
        runtime=GraphRuntime(),
        checkpointer=checkpointer,
    )
    result = await graph.ainvoke(
        {"companion_id": "demo", "last_user_message": "hello"},
        config={"configurable": {"thread_id": "demo"}},
    )
```

Run setup only during controlled initialization:

```python
from untamed_companion.checkpoint import PostgresCheckpointSettings

settings = PostgresCheckpointSettings(
    conn_string="postgresql://user:pass@localhost:5432/app",
    setup=True,
)

async with create_async_postgres_checkpointer(settings) as checkpointer:
    ...
```

The helper wraps LangGraph's `AsyncPostgresSaver.from_conn_string(...)` and
optionally calls `setup()`.

## FastAPI Thread IDs

When using the FastAPI route factory with a checkpointer, pass `config_factory`
so application-owned tenant/session IDs become LangGraph thread IDs:

```python
def config_factory(thread_id: str) -> dict[str, object]:
    return {"configurable": {"thread_id": f"tenant-a:{thread_id}"}}
```

The router calls `config_factory(companion_id)` for chat streams and
`config_factory(f"greeting:{companion_id}")` for greeting streams.
