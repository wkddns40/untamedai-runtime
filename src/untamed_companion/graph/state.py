"""State schemas for public companion graphs."""

from __future__ import annotations

from operator import add
from typing import Annotated, Literal, TypedDict

from untamed_companion.graph.events import CompanionEvent

NamingPhase = Literal["unnamed_idle", "awaiting_response", "named"]
UserTier = Literal["FREE", "SOULMATE"]
UserLang = Literal["ko", "en"]
MsgType = Literal["chat", "coffee_turn", "set_lang"]


class ChatState(TypedDict, total=False):
    """State passed through the chat graph.

    The schema mirrors the private runtime's public contract while avoiding
    product-specific prompt text or database coupling.
    """

    companion_id: str
    user_id: str
    user_tier: UserTier
    user_lang: UserLang
    user_name: str
    last_user_message: str
    msg_type: MsgType
    companion: dict[str, object]
    naming_phase: NamingPhase
    naming_prompted: bool
    naming_intent: dict[str, str | None]
    semantic_logs: list[dict[str, object]]
    recent_logs: list[dict[str, object]]
    emotions: list[dict[str, object]]
    weather_info: str
    system_prompt: str
    pending_ai_text: str
    force_naming_prompt: bool
    emit: Annotated[list[CompanionEvent], add]


class EmotionState(TypedDict, total=False):
    """State passed through the daily emotion graph."""

    companion_id: str
    target_date: str
    logs: list[dict[str, object]]
    system_prompt: str
    analysis: dict[str, object]
    new_summary: str
    skipped: bool
