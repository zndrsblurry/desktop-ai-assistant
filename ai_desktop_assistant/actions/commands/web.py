"""
Web Action Commands
"""

from typing import Optional, Type

# --- Import Argument Schemas ---
try:
    from ai_desktop_assistant.ai.tools.definitions import (
        SearchWebArgs,
        OpenUrlArgs,
        NavigateBrowserArgs,
        ScrapeWebsiteArgs,
    )
    from pydantic import BaseModel
except ImportError:

    class BaseModel:
        pass

    class SearchWebArgs(BaseModel):
        pass

    class OpenUrlArgs(BaseModel):
        pass

    class NavigateBrowserArgs(BaseModel):
        pass

    class ScrapeWebsiteArgs(BaseModel):
        pass


from .base import Command


class SearchWebCommand(Command):
    """Command to perform a web search using a specified engine."""

    ArgsSchema: Optional[Type[BaseModel]] = SearchWebArgs

    @property
    def action_id(self) -> str:
        return "search_web"


class OpenUrlCommand(Command):
    """Command to open a URL in the default web browser."""

    ArgsSchema: Optional[Type[BaseModel]] = OpenUrlArgs

    @property
    def action_id(self) -> str:
        return "open_url"


class NavigateBrowserCommand(Command):
    """Command to navigate within an active browser window (back, forward, refresh, etc.)."""

    ArgsSchema: Optional[Type[BaseModel]] = NavigateBrowserArgs

    @property
    def action_id(self) -> str:
        return "navigate_browser"


class ScrapeWebsiteCommand(Command):
    """Command to extract content from a specified webpage."""

    ArgsSchema: Optional[Type[BaseModel]] = ScrapeWebsiteArgs

    @property
    def action_id(self) -> str:
        return "scrape_website"
