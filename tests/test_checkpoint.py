import pytest

from untamed_companion.checkpoint.postgres import (
    PostgresCheckpointSettings,
    create_async_postgres_checkpointer,
)
from untamed_companion.exceptions import IntegrationNotConfiguredError


def test_postgres_checkpoint_settings_reject_empty_conn_string() -> None:
    with pytest.raises(ValueError, match="conn_string must not be empty"):
        PostgresCheckpointSettings(conn_string="")


async def test_async_postgres_checkpointer_reports_missing_extra(monkeypatch) -> None:
    import untamed_companion.checkpoint.postgres as postgres_module

    def fake_import(_name: str) -> object:
        raise ImportError("missing")

    monkeypatch.setattr(postgres_module, "import_module", fake_import)

    with pytest.raises(IntegrationNotConfiguredError, match="postgres"):
        async with create_async_postgres_checkpointer("postgresql://example/db"):
            raise AssertionError("context should not open")


async def test_async_postgres_checkpointer_uses_langgraph_saver(monkeypatch) -> None:
    import untamed_companion.checkpoint.postgres as postgres_module

    calls: list[tuple[object, ...]] = []

    class FakeCheckpointer:
        def __init__(self) -> None:
            self.setup_called = False

        async def setup(self) -> None:
            self.setup_called = True
            calls.append(("setup",))

    class FakeContext:
        def __init__(self, checkpointer: FakeCheckpointer) -> None:
            self.checkpointer = checkpointer

        async def __aenter__(self) -> FakeCheckpointer:
            calls.append(("enter",))
            return self.checkpointer

        async def __aexit__(self, *_exc: object) -> None:
            calls.append(("exit",))

    class FakeSaver:
        @classmethod
        def from_conn_string(cls, conn_string: str, **kwargs: object) -> FakeContext:
            calls.append(("from_conn_string", conn_string, kwargs))
            return FakeContext(FakeCheckpointer())

    class FakeModule:
        AsyncPostgresSaver = FakeSaver

    monkeypatch.setattr(postgres_module, "import_module", lambda _name: FakeModule)

    settings = PostgresCheckpointSettings(
        conn_string="postgresql://example/db",
        setup=True,
        pipeline=True,
    )
    async with create_async_postgres_checkpointer(settings) as checkpointer:
        assert checkpointer.setup_called is True

    assert calls == [
        ("from_conn_string", "postgresql://example/db", {"pipeline": True}),
        ("enter",),
        ("setup",),
        ("exit",),
    ]
