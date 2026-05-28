"""Optional LangGraph Postgres checkpointer helpers."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from importlib import import_module
from typing import Any

from untamed_companion.exceptions import IntegrationNotConfiguredError


@dataclass(frozen=True, slots=True)
class PostgresCheckpointSettings:
    """Settings for LangGraph's async Postgres checkpointer."""

    conn_string: str
    setup: bool = False
    pipeline: bool = False
    serde: Any | None = None

    def __post_init__(self) -> None:
        if not self.conn_string:
            raise ValueError("conn_string must not be empty")


@asynccontextmanager
async def create_async_postgres_checkpointer(
    settings: PostgresCheckpointSettings | str,
    *,
    setup: bool = False,
    pipeline: bool = False,
    serde: Any | None = None,
) -> AsyncIterator[Any]:
    """Create an async LangGraph Postgres checkpointer context manager.

    Pass `setup=True` only during controlled migrations or local initialization.
    Application services should normally run setup separately.
    """

    active_settings = (
        settings
        if isinstance(settings, PostgresCheckpointSettings)
        else PostgresCheckpointSettings(
            conn_string=settings,
            setup=setup,
            pipeline=pipeline,
            serde=serde,
        )
    )
    try:
        postgres_module = import_module("langgraph.checkpoint.postgres.aio")
    except ImportError as exc:
        raise IntegrationNotConfiguredError(
            "Postgres checkpointer requires "
            "`pip install untamedai-runtime[postgres]`."
        ) from exc

    saver_cls = postgres_module.AsyncPostgresSaver
    kwargs: dict[str, object] = {"pipeline": active_settings.pipeline}
    if active_settings.serde is not None:
        kwargs["serde"] = active_settings.serde

    async with saver_cls.from_conn_string(
        active_settings.conn_string,
        **kwargs,
    ) as checkpointer:
        if active_settings.setup:
            await checkpointer.setup()
        yield checkpointer
