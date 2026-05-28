"""Greeting graph node."""

from __future__ import annotations

from untamed_companion.graph.events import event
from untamed_companion.graph.runtime import GraphRuntime
from untamed_companion.graph.state import ChatState


async def generate_greeting(
    state: ChatState, runtime: GraphRuntime
) -> dict[str, object]:
    """Generate first greeting."""

    text = await runtime.resolve_greeting_responder().generate_greeting(state)
    return {"emit": [event("greeting", text)]}

