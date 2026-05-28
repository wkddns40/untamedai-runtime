"""Shared package exceptions."""


class UntamedCompanionError(Exception):
    """Base exception for package-level errors."""


class IntegrationNotConfiguredError(UntamedCompanionError):
    """Raised when an optional integration is requested but not configured."""

