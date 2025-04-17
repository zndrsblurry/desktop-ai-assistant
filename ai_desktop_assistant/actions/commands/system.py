"""
System Action Commands
"""

from typing import Optional, Type

# --- Import Argument Schemas ---
try:
    from ai_desktop_assistant.ai.tools.definitions import (
        LaunchApplicationArgs,
        CloseApplicationArgs,
        GetSystemInfoArgs,
        OpenFileArgs,
        ListDirectoryArgs,
        CaptureScreenArgs,
        AnalyzeScreenArgs,
        DeleteFileArgs,
        AdjustVolumeArgs,
    )
    from pydantic import BaseModel
except ImportError:

    class BaseModel:
        pass

    class LaunchApplicationArgs(BaseModel):
        pass

    class CloseApplicationArgs(BaseModel):
        pass

    class GetSystemInfoArgs(BaseModel):
        pass

    class OpenFileArgs(BaseModel):
        pass

    class ListDirectoryArgs(BaseModel):
        pass

    class CaptureScreenArgs(BaseModel):
        pass

    class AnalyzeScreenArgs(BaseModel):
        pass

    class DeleteFileArgs(BaseModel):
        pass

    class AdjustVolumeArgs(BaseModel):
        pass


from .base import Command


class LaunchApplicationCommand(Command):
    """Command to launch an application by name or path."""

    ArgsSchema: Optional[Type[BaseModel]] = LaunchApplicationArgs

    @property
    def action_id(self) -> str:
        # Use consistent name from tool definition
        return "launch_application"


class CloseApplicationCommand(Command):
    """Command to close an application window by name or title."""

    ArgsSchema: Optional[Type[BaseModel]] = CloseApplicationArgs

    @property
    def action_id(self) -> str:
        return "close_application"


class GetSystemInfoCommand(Command):
    """Command to retrieve basic or detailed system information."""

    ArgsSchema: Optional[Type[BaseModel]] = GetSystemInfoArgs

    @property
    def action_id(self) -> str:
        return "get_system_info"


# --- File Commands (often handled by System Executor) ---


class OpenFileCommand(Command):
    """Command to open a file with its default application."""

    ArgsSchema: Optional[Type[BaseModel]] = OpenFileArgs

    @property
    def action_id(self) -> str:
        return "open_file"


class ListDirectoryCommand(Command):
    """Command to list the contents of a directory."""

    ArgsSchema: Optional[Type[BaseModel]] = ListDirectoryArgs

    @property
    def action_id(self) -> str:
        return "list_directory"


class CaptureScreenCommand(Command):
    """Command to capture a screenshot of the entire screen or specific region."""

    ArgsSchema: Optional[Type[BaseModel]] = CaptureScreenArgs

    @property
    def action_id(self) -> str:
        return "capture_screen"


class AnalyzeScreenCommand(Command):
    """Command to analyze screen content using computer vision and OCR."""

    ArgsSchema: Optional[Type[BaseModel]] = AnalyzeScreenArgs

    @property
    def action_id(self) -> str:
        return "analyze_screen"


class DeleteFileCommand(Command):
    """Command to delete a file from the filesystem."""

    ArgsSchema: Optional[Type[BaseModel]] = DeleteFileArgs

    @property
    def action_id(self) -> str:
        return "delete_file"


class AdjustVolumeCommand(Command):
    """Command to adjust system audio volume."""

    ArgsSchema: Optional[Type[BaseModel]] = AdjustVolumeArgs

    @property
    def action_id(self) -> str:
        return "adjust_volume"
