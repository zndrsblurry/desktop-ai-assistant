# Location: ai_desktop_assistant/core/exceptions.py
"""
Custom Exception Classes

This module defines custom exceptions used throughout the application.
"""


class AIAssistantError(Exception):
    """Base exception class for all AI Assistant errors."""

    pass


class InitializationError(AIAssistantError):
    """Raised when a component fails to initialize."""

    pass


class APIError(AIAssistantError):
    """Raised when there's an error communicating with an external API."""

    pass


class InputError(AIAssistantError):
    """Raised when there's an error with input processing."""

    pass


class OutputError(AIAssistantError):
    """Raised when there's an error with output processing."""

    pass


class ActionError(AIAssistantError):
    """Raised when there's an error executing an action."""

    pass


class ConfigurationError(AIAssistantError):
    """Raised when there's an issue with configuration."""

    pass


class SecurityError(AIAssistantError):
    """Raised for security-related issues."""

    pass
