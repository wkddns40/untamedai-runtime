"""Greeting graph builder."""

from __future__ import annotations

from typing import Any

from langgraph.graph import END, START, StateGraph

from untamed_companion.graph.nodes.greeting import generate_greeting
from untamed_companion.graph.runtime import GraphRuntime
from untamed_companion.graph.state import ChatState


def _bind(runtime: GraphRuntime) -> Any:
    async def _node(state: ChatState) -> dict[str, object]:
        return await generate_greeting(state, runtime)

    return _node


def build_greeting_graph(
    *, runtime: GraphRuntime | None = None, checkpointer: Any | None = None
) -> Any:
    """Build the public greeting graph."""

    graph: Any = StateGraph(ChatState)
    graph.add_node("generate_greeting", _bind(runtime or GraphRuntime()))
    graph.add_edge(START, "generate_greeting")
    graph.add_edge("generate_greeting", END)
    compile_kwargs: dict[str, object] = {}
    if checkpointer is not None:
        compile_kwargs["checkpointer"] = checkpointer
    return graph.compile(**compile_kwargs)
