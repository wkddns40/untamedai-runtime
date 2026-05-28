"""Prompt provider interfaces and default implementations."""

from untamed_companion.prompts.base import PromptProvider
from untamed_companion.prompts.default import (
    DefaultPromptProvider,
    StaticPromptProvider,
)

__all__ = ["DefaultPromptProvider", "PromptProvider", "StaticPromptProvider"]
