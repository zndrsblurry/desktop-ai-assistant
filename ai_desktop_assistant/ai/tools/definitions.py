"""
Tool Function Definitions for AI Desktop Assistant

This module defines the actual Python functions that implement the logic
for each tool. These functions are decorated with @register_tool from the
registry, including their Pydantic argument schemas.

Each function typically:
1. Takes arguments defined in its corresponding Pydantic schema.
2. Performs necessary validation or processing.
3. Publishes an ACTION_REQUESTED event via the global _EVENT_BUS.
4. Returns a dictionary confirming the request was published (actual result
   comes asynchronously via events).
"""

import logging
from typing import Dict, List, Any, Optional

# Use Pydantic for defining structured arguments for tools
try:
    from pydantic import BaseModel, Field, validator

    PYDANTIC_AVAILABLE = True
except ImportError:
    # Should have been caught by registry, but double-check
    logging.critical("Pydantic not found. Tool definitions cannot be processed.")

    # Define dummy classes if needed for static analysis, but runtime will fail
    class BaseModel:
        pass

    def Field(*args, **kwargs):
        return None

    def validator(*args, **kwargs):
        return lambda func: func

    PYDANTIC_AVAILABLE = False


# Local imports
from .registry import register_tool  # Import the decorator
from ai_desktop_assistant.core.events import EventBus, Events

# from ai_desktop_assistant.core.exceptions import (
#     ActionExecutionError,
# )  # May not be raised here directly, but good practice

# --- Global Event Bus Reference ---
# This MUST be set by calling initialize_tools() from core/app.py during startup
_EVENT_BUS: Optional[EventBus] = None
logger = logging.getLogger(__name__)


def initialize_tools(event_bus: EventBus) -> None:
    """
    Initializes the tool definitions module with the application's event bus.
    Must be called before any tool function is invoked by the AI/agent.

    Args:
        event_bus: The application's central event bus instance.
    """
    global _EVENT_BUS
    if not _EVENT_BUS:
        _EVENT_BUS = event_bus
        logger.info("Tool Definitions initialized with EventBus.")
    else:
        logger.warning("Tool Definitions already initialized.")


# --- Helper Function ---
async def _publish_action_request(
    action_id: str, parameters: Dict[str, Any]
) -> Dict[str, Any]:
    """Helper to publish action request event and return standard confirmation."""
    if not _EVENT_BUS:
        error_msg = (
            f"EventBus not initialized for tool '{action_id}'. Cannot execute action."
        )
        logger.error(error_msg)
        # This dictionary might be returned to LangChain/AI, indicating failure clearly.
        return {"success": False, "error": error_msg}

    try:
        # Sanitize parameters slightly for logging if needed (e.g., truncate long text)
        log_params = {
            k: (v[:50] + "..." if isinstance(v, str) and len(v) > 50 else v)
            for k, v in parameters.items()
        }
        logger.info(
            f"Tool Definition '{action_id}': Publishing ACTION_REQUESTED event with params: {log_params}"
        )

        await _EVENT_BUS.publish(
            Events.ACTION_REQUESTED,
            {
                "action_id": action_id,
                "parameters": parameters,
                "source": "tool_definition",  # Indicate origin
            },
        )
        # This return value confirms the *request* was sent successfully.
        # The actual success/failure/data comes back asynchronously via events.
        # Return a message that LangChain/AI can understand.
        return {
            "status": "Action requested successfully. Waiting for execution result."
        }
    except Exception as e:
        logger.exception(f"Error publishing action request for {action_id}: {e}")
        return {
            "success": False,
            "error": f"Failed to publish request for action '{action_id}': {e}",
        }


# --- Tool Argument Schemas (Defined using Pydantic) ---
# These define the expected input structure for each tool's function.


class MoveMouseArgs(BaseModel):
    x: int = Field(
        ...,
        description="Target X coordinate (horizontal pixels from left edge of the screen or specified monitor)",
    )
    y: int = Field(
        ...,
        description="Target Y coordinate (vertical pixels from top edge of the screen or specified monitor)",
    )
    monitor_id: Optional[int] = Field(
        None,
        description="Optional: Target monitor ID (e.g., 0 for primary, 1 for secondary). If None, uses primary or current.",
    )
    description: Optional[str] = Field(
        None,
        description="Optional: Visual description of the target (e.g., 'OK button', 'File menu') to aid potential adaptive movement.",
    )


class ClickMouseArgs(BaseModel):
    button: str = Field(
        "left", description="Mouse button to click ('left', 'right', or 'middle')"
    )
    double: bool = Field(
        False,
        description="Set to true to perform a double-click instead of a single click.",
    )

    @validator("button")
    def button_must_be_valid(cls, v):
        if v.lower() not in ["left", "right", "middle"]:
            raise ValueError("button must be 'left', 'right', or 'middle'")
        return v.lower()


class DragMouseArgs(BaseModel):
    to_x: int = Field(
        ..., description="Destination X coordinate to drag the mouse cursor to."
    )
    to_y: int = Field(
        ..., description="Destination Y coordinate to drag the mouse cursor to."
    )
    # from_x, from_y could be added if needed, but usually drag starts from current position
    monitor_id: Optional[int] = Field(
        None, description="Optional: Target monitor ID for the destination coordinates."
    )


class ScrollMouseArgs(BaseModel):
    dx: int = Field(
        0, description="Amount to scroll horizontally (positive right, negative left)."
    )
    dy: int = Field(
        0, description="Amount to scroll vertically (positive down, negative up)."
    )  # Changed to match common convention


class TypeTextArgs(BaseModel):
    text: str = Field(
        ..., description="The exact text string to type using the keyboard."
    )
    delay: Optional[float] = Field(
        None,
        description="Optional: Delay in seconds between typing each character to simulate human speed (e.g., 0.05). If None, uses default typing speed.",
    )


class PressKeyArgs(BaseModel):
    key: str = Field(
        ...,
        description="Name of the key to press (e.g., 'enter', 'tab', 'a', 'f5', 'esc', 'win', 'cmd', 'ctrl', 'alt', 'shift'). For combinations, specify modifiers separately.",
    )
    modifiers: Optional[List[str]] = Field(
        None,
        description="Optional: List of modifier keys to hold down while pressing the main key (e.g., ['ctrl', 'shift']). Valid modifiers: 'ctrl', 'alt', 'shift', 'cmd' (or 'win'/'meta'), 'option' (maps to alt).",
    )


class CaptureScreenArgs(BaseModel):
    monitor_id: Optional[int] = Field(
        None,
        description="Optional: Monitor ID to capture (e.g., 0 for primary). If None, captures the primary monitor or the one containing the active window.",
    )
    region: Optional[Dict[str, int]] = Field(
        None,
        description="Optional: Specific region to capture relative to the monitor as {'x': int, 'y': int, 'width': int, 'height': int}. If None, captures the full monitor.",
    )
    save_path: Optional[str] = Field(
        None,
        description="Optional: File path to save the screenshot image to. If None, the image data is returned for analysis.",
    )


class AnalyzeScreenArgs(BaseModel):
    description: str = Field(
        ...,
        description="Detailed description of the UI element or area to find (e.g., 'the blue login button', 'text input field labeled Username', 'find the error message text').",
    )
    monitor_id: Optional[int] = Field(
        None,
        description="Optional: Monitor ID to analyze. If None, analyzes the primary monitor or the one with the active window.",
    )
    ocr: bool = Field(
        True, description="Whether to use OCR to read text during analysis."
    )  # Example extra param


class LaunchApplicationArgs(BaseModel):
    name_or_path: str = Field(
        ...,
        description="The name of the application (e.g., 'Notepad', 'Google Chrome') or the full path to its executable.",
    )


class CloseApplicationArgs(BaseModel):
    name_or_title: str = Field(
        ...,
        description="The name of the application (e.g., 'Notepad') or the exact title of the window to close.",
    )


class GetSystemInfoArgs(BaseModel):
    detail_level: str = Field(
        "basic", description="Level of detail required ('basic' or 'full')."
    )  # Example argument


class SearchWebArgs(BaseModel):
    query: str = Field(..., description="The search query string.")
    engine: Optional[str] = Field(
        "duckduckgo",
        description="Optional: Search engine to use ('duckduckgo', 'google', 'bing'). Defaults to duckduckgo.",
    )
    max_results: Optional[int] = Field(
        5,
        description="Optional: Maximum number of search results to return (if applicable to the engine/method).",
    )


class OpenUrlArgs(BaseModel):
    url: str = Field(
        ...,
        description="The full URL (including http:// or https://) to open in the default web browser.",
    )


class OpenFileArgs(BaseModel):
    path: str = Field(
        ...,
        description="The full, absolute path to the file to open with its default application.",
    )


class ListDirectoryArgs(BaseModel):
    path: str = Field(
        ".",
        description="Directory path to list contents of. Defaults to the current working directory if not specified.",
    )
    recursive: bool = Field(
        False,
        description="Set to true to list contents recursively (use with caution).",
    )  # Example


class ExecutePythonCodeArgs(BaseModel):
    code: str = Field(
        ...,
        description="The Python code snippet to execute. Must be safe and not interact with system resources unless explicitly designed for it.",
    )
    timeout: Optional[float] = Field(
        10.0, description="Optional: Maximum execution time in seconds."
    )


class DeleteFileArgs(BaseModel):
    path: str = Field(..., description="Full path to the file that should be deleted.")
    force: bool = Field(
        False,
        description="Whether to force deletion without additional checks (use with caution).",
    )


class AdjustVolumeArgs(BaseModel):
    level: int = Field(..., description="Volume level to set (0-100).", ge=0, le=100)
    device: Optional[str] = Field(
        None,
        description="Optional: Specific audio device to adjust. If None, adjusts system default.",
    )

    @validator("level")
    def validate_volume_level(cls, v):
        if not 0 <= v <= 100:
            raise ValueError("Volume level must be between 0 and 100")
        return v


class NavigateBrowserArgs(BaseModel):
    action: str = Field(
        ...,
        description="Navigation action to perform ('back', 'forward', 'refresh', 'stop', 'home')",
    )
    tab_id: Optional[int] = Field(
        None,
        description="Optional: Specific browser tab ID to navigate. If None, uses the active tab.",
    )

    @validator("action")
    def validate_action(cls, v):
        valid_actions = {"back", "forward", "refresh", "stop", "home"}
        if v.lower() not in valid_actions:
            raise ValueError(f"action must be one of: {', '.join(valid_actions)}")
        return v.lower()


class ScrapeWebsiteArgs(BaseModel):
    url: str = Field(
        ...,
        description="The URL of the webpage to scrape content from.",
    )
    elements: Optional[List[str]] = Field(
        None,
        description="Optional: List of CSS selectors or element descriptions to specifically target (e.g., ['h1', '.main-content', '#article-text']). If None, extracts main content.",
    )
    include_images: bool = Field(
        False,
        description="Whether to include image URLs and alt text in the scraped content.",
    )
    max_depth: Optional[int] = Field(
        1,
        description="Maximum depth for nested content extraction. Use with caution for larger values.",
        ge=1,
        le=5,
    )


# --- Tool Function Definitions ---
# Each function acts as an entry point for the AI. It validates parameters (implicitly via Pydantic)
# and then dispatches an event for the corresponding executor to handle the actual work.


@register_tool(args_schema=MoveMouseArgs, category="mouse", name="move_mouse")
async def move_mouse_tool(
    x: int, y: int, monitor_id: Optional[int] = None, description: Optional[str] = None
) -> Dict[str, Any]:
    """Moves the mouse cursor smoothly to the specified screen coordinates (x, y). Optionally targets a specific monitor or uses a visual description."""
    return await _publish_action_request(
        "move_mouse",
        {"x": x, "y": y, "monitor_id": monitor_id, "description": description},
    )


@register_tool(args_schema=ClickMouseArgs, category="mouse", name="click_mouse")
async def click_mouse_tool(
    button: str = "left", double: bool = False
) -> Dict[str, Any]:
    """Performs a mouse click (left, right, or middle) at the current cursor position. Can optionally perform a double-click."""
    return await _publish_action_request(
        "click_mouse", {"button": button, "double": double}
    )


@register_tool(args_schema=DragMouseArgs, category="mouse", name="drag_mouse")
async def drag_mouse_tool(
    to_x: int, to_y: int, monitor_id: Optional[int] = None
) -> Dict[str, Any]:
    """Presses and holds the left mouse button, drags the cursor from its current position to the destination coordinates (to_x, to_y), then releases."""
    return await _publish_action_request(
        "drag_mouse", {"to_x": to_x, "to_y": to_y, "monitor_id": monitor_id}
    )


@register_tool(args_schema=ScrollMouseArgs, category="mouse", name="scroll_mouse")
async def scroll_mouse_tool(dx: int = 0, dy: int = 0) -> Dict[str, Any]:
    """Scrolls the mouse wheel vertically (dy) or horizontally (dx). Positive dy scrolls down, negative dy scrolls up."""
    return await _publish_action_request("scroll_mouse", {"dx": dx, "dy": dy})


@register_tool(args_schema=TypeTextArgs, category="keyboard", name="type_text")
async def type_text_tool(text: str, delay: Optional[float] = None) -> Dict[str, Any]:
    """Types the provided text string using the keyboard. Can simulate human typing speed with an optional delay between characters."""
    return await _publish_action_request("type_text", {"text": text, "delay": delay})


@register_tool(args_schema=PressKeyArgs, category="keyboard", name="press_key")
async def press_key_tool(
    key: str, modifiers: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Presses a specific keyboard key (like 'enter', 'esc', 'f1', 'a'). Can also hold modifier keys ('ctrl', 'alt', 'shift', 'cmd'/'win') simultaneously."""
    return await _publish_action_request(
        "press_key", {"key": key, "modifiers": modifiers or []}
    )


@register_tool(args_schema=CaptureScreenArgs, category="screen", name="capture_screen")
async def capture_screen_tool(
    monitor_id: Optional[int] = None,
    region: Optional[Dict[str, int]] = None,
    save_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Captures an image of the entire screen, a specific monitor, or a defined region. Can optionally save the image to a file."""
    return await _publish_action_request(
        "capture_screen",
        {"monitor_id": monitor_id, "region": region, "save_path": save_path},
    )


@register_tool(args_schema=AnalyzeScreenArgs, category="screen", name="analyze_screen")
async def analyze_screen_tool(
    description: str, monitor_id: Optional[int] = None, ocr: bool = True
) -> Dict[str, Any]:
    """Analyzes the screen (or a specific monitor) using computer vision and OCR to find UI elements or text matching the description. Returns coordinates or text found."""
    return await _publish_action_request(
        "analyze_screen",
        {"description": description, "monitor_id": monitor_id, "ocr": ocr},
    )


@register_tool(
    args_schema=LaunchApplicationArgs, category="system", name="launch_application"
)
async def launch_application_tool(name_or_path: str) -> Dict[str, Any]:
    """Launches an application specified by its name (e.g., 'Chrome') or its full executable path."""
    return await _publish_action_request(
        "launch_application", {"name": name_or_path}
    )  # Use name consistently


@register_tool(
    args_schema=CloseApplicationArgs, category="system", name="close_application"
)
async def close_application_tool(name_or_title: str) -> Dict[str, Any]:
    """Closes an application window identified by its name or window title."""
    return await _publish_action_request(
        "close_application", {"name_or_title": name_or_title}
    )


@register_tool(args_schema=GetSystemInfoArgs, category="system", name="get_system_info")
async def get_system_info_tool(detail_level: str = "basic") -> Dict[str, Any]:
    """Retrieves information about the operating system, hardware (CPU, memory), and user."""
    return await _publish_action_request(
        "get_system_info", {"detail_level": detail_level}
    )


@register_tool(args_schema=SearchWebArgs, category="web", name="search_web")
async def search_web_tool(
    query: str, engine: Optional[str] = "duckduckgo", max_results: Optional[int] = 5
) -> Dict[str, Any]:
    """Performs a web search using the specified engine (default: duckduckgo) and returns a summary of the results."""
    return await _publish_action_request(
        "search_web", {"query": query, "engine": engine, "max_results": max_results}
    )


@register_tool(args_schema=OpenUrlArgs, category="web", name="open_url")
async def open_url_tool(url: str) -> Dict[str, Any]:
    """Opens the given URL in the system's default web browser."""
    return await _publish_action_request("open_url", {"url": url})


@register_tool(args_schema=OpenFileArgs, category="file", name="open_file")
async def open_file_tool(path: str) -> Dict[str, Any]:
    """Opens a specified file using the default application associated with its file type."""
    return await _publish_action_request("open_file", {"path": path})


@register_tool(args_schema=ListDirectoryArgs, category="file", name="list_directory")
async def list_directory_tool(
    path: str = ".", recursive: bool = False
) -> Dict[str, Any]:
    """Lists the files and subdirectories within the specified directory path. Can optionally list recursively."""
    return await _publish_action_request(
        "list_directory", {"path": path, "recursive": recursive}
    )


@register_tool(args_schema=NavigateBrowserArgs, category="web", name="navigate_browser")
async def navigate_browser_tool(
    action: str, tab_id: Optional[int] = None
) -> Dict[str, Any]:
    """Performs browser navigation actions like back, forward, refresh on the active or specified browser tab."""
    return await _publish_action_request(
        "navigate_browser", {"action": action, "tab_id": tab_id}
    )


@register_tool(args_schema=ScrapeWebsiteArgs, category="web", name="scrape_website")
async def scrape_website_tool(
    url: str,
    elements: Optional[List[str]] = None,
    include_images: bool = False,
    max_depth: Optional[int] = 1,
) -> Dict[str, Any]:
    """Extracts content from a specified webpage using web scraping techniques."""
    return await _publish_action_request(
        "scrape_website",
        {
            "url": url,
            "elements": elements,
            "include_images": include_images,
            "max_depth": max_depth,
        },
    )


# --- Potentially Dangerous Code Execution Tool ---
# Only register if code execution is explicitly enabled and understood to be risky.
# from ai_desktop_assistant.core.config import AppConfig # Need config access
# if AppConfig(...).enable_code_execution: # How to access config here safely? Maybe check via env var at import time?
# @register_tool(args_schema=ExecutePythonCodeArgs, category="code", name="execute_python_code", enabled=False) # Disabled by default
# async def execute_python_code_tool(code: str, timeout: Optional[float] = 10.0) -> Dict[str, Any]:
#     """Executes a provided snippet of Python code in a restricted environment. Use with extreme caution. Returns stdout, stderr, and success status."""
#     # Add extra safety checks/warnings here before publishing
#     logger.warning("Executing potentially dangerous code execution tool!")
#     # if "os." in code or "subprocess." in code: # Example naive check
#     #     return {"success": False, "error": "Code execution blocked due to potentially unsafe operations."}
#     return await _publish_action_request("execute_python_code", {"code": code, "timeout": timeout})
