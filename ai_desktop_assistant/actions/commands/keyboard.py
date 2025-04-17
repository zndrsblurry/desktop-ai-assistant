"""
Keyboard Action Commands
"""

from typing import Optional, Type

# --- Import Argument Schemas ---
try:
    from ai_desktop_assistant.ai.tools.definitions import TypeTextArgs, PressKeyArgs
    from pydantic import BaseModel
except ImportError:

    class BaseModel:
        pass

    class TypeTextArgs(BaseModel):
        pass

    class PressKeyArgs(BaseModel):
        pass


from .base import Command


class TypeTextCommand(Command):
    """Command to type a given string using the keyboard."""

    ArgsSchema: Optional[Type[BaseModel]] = TypeTextArgs

    @property
    def action_id(self) -> str:
        return "type_text"


class PressKeyCommand(Command):
    """Command to press a specific key or key combination with modifiers."""

    ArgsSchema: Optional[Type[BaseModel]] = PressKeyArgs

    @property
    def action_id(self) -> str:
        return "press_key"
