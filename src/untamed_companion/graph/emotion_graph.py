"""Daily emotion graph builder."""

from __future__ import annotations

from typing import Any

from langgraph.graph import END, START, StateGraph

from untamed_companion.graph.nodes.emotion import analyze_emotion
from untamed_companion.graph.runtime import GraphRuntime
from untamed_companion.graph.state import EmotionState


def _bind(runtime: GraphRuntime) -> Any:
    async def _node(state: EmotionState) -> dict[str, object]:
        return await analyze_emotion(state, runtime)

    return _node


def build_emotion_graph(
    *, runtime: GraphRuntime | None = None, checkpointer: Any | None = None
) -> Any:
    """Build the public daily emotion graph."""

    graph: Any = StateGraph(EmotionState)
    graph.add_node("analyze_emotion", _bind(runtime or GraphRuntime()))
    graph.add_edge(START, "analyze_emotion")
    graph.add_edge("analyze_emotion", END)
    compile_kwargs: dict[str, object] = {}
    if checkpointer is not None:
        compile_kwargs["checkpointer"] = checkpointer
    return graph.compile(**compile_kwargs)
