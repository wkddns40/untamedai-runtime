"""Greeting graph node."""

from __future__ import annotations

from typing import cast

from untamed_companion.graph.events import event
from untamed_companion.graph.runtime import GraphRuntime
from untamed_companion.graph.state import ChatState


async def generate_greeting(
    state: ChatState, runtime: GraphRuntime
) -> dict[str, object]:
    """Generate first greeting."""

    prompted_state = dict(state)
    prompted_state["system_prompt"] = (
        runtime.resolve_prompt_provider().build_greeting_prompt(state)
    )
    text = await runtime.resolve_greeting_responder().generate_greeting(
        cast(ChatState, prompted_state)
    )
    return {
        "system_prompt": prompted_state["system_prompt"],
        "emit": [event("greeting", text)],
    }
