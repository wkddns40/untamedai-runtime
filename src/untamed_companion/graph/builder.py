"""Chat graph builder."""

from __future__ import annotations

from typing import Any, cast

from langgraph.graph import END, START, StateGraph

from untamed_companion.graph.nodes import chat
from untamed_companion.graph.runtime import GraphRuntime
from untamed_companion.graph.state import ChatState


def _bind(
    fn: Any,
    runtime: GraphRuntime,
) -> Any:
    async def _node(state: ChatState) -> dict[str, object]:
        result = await fn(state, runtime)
        return cast(dict[str, object], result)

    return _node


def build_chat_graph(
    *,
    runtime: GraphRuntime | None = None,
    checkpointer: Any | None = None,
    store: Any | None = None,
) -> Any:
    """Build the public chat graph.

    `store` is accepted for forward compatibility with LangGraph compile
    options and later store integration.
    """

    active_runtime = runtime or GraphRuntime()
    graph: Any = StateGraph(ChatState)
    graph.add_node("load_session", _bind(chat.load_session, active_runtime))
    graph.add_node("intake", _bind(chat.intake, active_runtime))
    graph.add_node("handle_coffee_turn", _bind(chat.handle_coffee_turn, active_runtime))
    graph.add_node(
        "handle_awaiting_naming", _bind(chat.handle_awaiting_naming, active_runtime)
    )
    graph.add_node(
        "detect_naming_intent",
        _bind(chat.detect_naming_intent, active_runtime),
    )
    graph.add_node("apply_ai_name", _bind(chat.apply_ai_name, active_runtime))
    graph.add_node("apply_user_name", _bind(chat.apply_user_name, active_runtime))
    graph.add_node("retrieve_memory", _bind(chat.retrieve_memory, active_runtime))
    graph.add_node("compose_prompt", _bind(chat.compose_prompt, active_runtime))
    graph.add_node("generate_response", _bind(chat.generate_response, active_runtime))
    graph.add_node("persist_messages", _bind(chat.persist_messages, active_runtime))
    graph.add_node(
        "check_naming_ceremony",
        _bind(chat.check_naming_ceremony, active_runtime),
    )

    graph.add_edge(START, "load_session")
    graph.add_edge("load_session", "intake")
    graph.add_conditional_edges(
        "intake",
        chat.route_after_intake,
        ["handle_coffee_turn", "handle_awaiting_naming", "detect_naming_intent"],
    )
    graph.add_conditional_edges(
        "handle_awaiting_naming",
        chat.route_after_awaiting,
        ["persist_messages", "detect_naming_intent"],
    )
    graph.add_conditional_edges(
        "detect_naming_intent",
        chat.route_naming_intent,
        ["apply_ai_name", "apply_user_name", "retrieve_memory"],
    )
    graph.add_edge("apply_user_name", "retrieve_memory")
    graph.add_edge("retrieve_memory", "compose_prompt")
    graph.add_edge("compose_prompt", "generate_response")
    for node in ("handle_coffee_turn", "apply_ai_name", "generate_response"):
        graph.add_edge(node, "persist_messages")
    graph.add_edge("persist_messages", "check_naming_ceremony")
    graph.add_edge("check_naming_ceremony", END)

    compile_kwargs: dict[str, object] = {}
    if checkpointer is not None:
        compile_kwargs["checkpointer"] = checkpointer
    if store is not None:
        compile_kwargs["store"] = store
    return graph.compile(**compile_kwargs)
