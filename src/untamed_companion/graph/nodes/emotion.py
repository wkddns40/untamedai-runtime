"""Daily emotion graph node."""

from __future__ import annotations

from untamed_companion.graph.runtime import GraphRuntime
from untamed_companion.graph.state import EmotionState


async def analyze_emotion(
    state: EmotionState, runtime: GraphRuntime
) -> dict[str, object]:
    """Analyze daily logs or mark the day skipped."""

    logs = state.get("logs") or []
    if not logs:
        return {"skipped": True, "analysis": {}, "new_summary": ""}
    analysis = await runtime.resolve_emotion_analyzer().analyze_emotion(state)
    return {
        "skipped": False,
        "analysis": analysis,
        "new_summary": str(analysis.get("summary_text") or ""),
    }

