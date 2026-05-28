"""Prompt provider protocol for runtime prompt composition."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from untamed_companion.graph.state import ChatState, EmotionState


class PromptProvider(Protocol):
    """Build system prompts for public runtime graphs."""

    def build_chat_prompt(self, state: ChatState) -> str:
        """Return the chat turn system prompt."""

    def build_greeting_prompt(self, state: ChatState) -> str:
        """Return the first-greeting system prompt."""

    def build_emotion_prompt(self, state: EmotionState) -> str:
        """Return the daily emotion analysis system prompt."""
