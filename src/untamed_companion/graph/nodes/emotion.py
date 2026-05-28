"""Daily emotion graph node."""

from __future__ import annotations

from typing import cast

from untamed_companion.graph.runtime import GraphRuntime
from untamed_companion.graph.state import EmotionState


async def analyze_emotion(
    state: EmotionState, runtime: GraphRuntime
) -> dict[str, object]:
    """Analyze daily logs or mark the day skipped."""

    logs = state.get("logs") or []
    if not logs:
        return {"skipped": True, "analysis": {}, "new_summary": ""}
    prompted_state = dict(state)
    prompted_state["system_prompt"] = (
        runtime.resolve_prompt_provider().build_emotion_prompt(state)
    )
    analysis = await runtime.resolve_emotion_analyzer().analyze_emotion(
        cast(EmotionState, prompted_state)
    )
    return {
        "skipped": False,
        "system_prompt": prompted_state["system_prompt"],
        "analysis": analysis,
        "new_summary": str(analysis.get("summary_text") or ""),
    }
