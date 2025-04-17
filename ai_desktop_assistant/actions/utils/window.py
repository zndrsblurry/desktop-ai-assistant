"""
Window Management Utilities

Provides cross-platform functions for interacting with application windows,
such as finding, activating, closing, resizing, and getting information.
Relies on libraries like pygetwindow or platform-specific APIs.
"""

import logging
import platform
import time
from typing import Optional, Dict, List, Any, Tuple

# Use pygetwindow for cross-platform basics
IS_WINDOWS = platform.system() == "Windows"
IS_MACOS = platform.system() == "Darwin"
IS_LINUX = platform.system() == "Linux"

if IS_WINDOWS:
    try:
        import pygetwindow as gw
        import ctypes  # For specific WinAPI calls if needed

        PYGETWINDOW_AVAILABLE = True
    except ImportError:
        logging.warning(
            "pygetwindow not found. Window management features limited on Windows. Install with: pip install pygetwindow"
        )
        gw = None
        ctypes = None
        PYGETWINDOW_AVAILABLE = False
elif IS_MACOS:
    try:
        # Prefer AppKit for more robust control on macOS
        import AppKit
        from Quartz import (
            CGWindowListCopyWindowInfo,
            kCGWindowListOptionOnScreenOnly,
            kCGNullWindowID,
            kCGWindowOwnerName,
            kCGWindowNumber,
            kCGWindowName,
        )

        MACOS_NATIVE_AVAILABLE = True
        # Fallback check for pygetwindow
        try:
            import pygetwindow as gw

            PYGETWINDOW_AVAILABLE = True
        except ImportError:
            gw = None
            PYGETWINDOW_AVAILABLE = False
    except ImportError:
        logging.warning(
            "AppKit/Quartz (pyobjc) not found. Window management features limited on macOS."
        )
        AppKit = None
        CGWindowListCopyWindowInfo = None  # Make linters happy
        kCGWindowListOptionOnScreenOnly = None
        kCGNullWindowID = None
        kCGWindowOwnerName = None
        kCGWindowNumber = None
        kCGWindowName = None
        MACOS_NATIVE_AVAILABLE = False
        # Check pygetwindow as final fallback
        try:
            import pygetwindow as gw

            PYGETWINDOW_AVAILABLE = True
        except ImportError:
            gw = None
            PYGETWINDOW_AVAILABLE = False

elif IS_LINUX:
    # pygetwindow often works on Linux with X11/Wayland dependencies installed
    try:
        import pygetwindow as gw

        # Potential need for python-xlib or other backends for gw
        PYGETWINDOW_AVAILABLE = True
    except ImportError:
        logging.warning(
            "pygetwindow not found. Window management features limited on Linux. Install with: pip install pygetwindow"
        )
        gw = None
        PYGETWINDOW_AVAILABLE = False
    # Consider alternative Linux libraries like 'ewmh' if pygetwindow is insufficient
else:  # Other platforms
    gw = None
    PYGETWINDOW_AVAILABLE = False
    MACOS_NATIVE_AVAILABLE = False


logger = logging.getLogger(__name__)

# Type hint for window objects (can vary by library)
WindowObject = Any


def list_windows(all_windows: bool = False) -> List[Dict[str, Any]]:
    """
    Lists currently open windows.

    Args:
        all_windows: If True, attempts to list all windows, including potentially
                     hidden or background ones (behavior depends on library).
                     If False (default), tries to list only visible application windows.

    Returns:
        A list of dictionaries, each containing info about a window (e.g., 'title', 'id', 'rect').
        Returns an empty list on failure or if library unavailable.
    """
    windows_info = []
    logger.debug(f"Listing windows (All: {all_windows})...")

    # macOS Native (Quartz) - often provides more info
    if IS_MACOS and MACOS_NATIVE_AVAILABLE and CGWindowListCopyWindowInfo:
        try:
            # kCGWindowListExcludeDesktopElements | kCGWindowListOptionOnScreenOnly
            # Experiment with options for desired window types
            options = kCGWindowListOptionOnScreenOnly
            window_list = CGWindowListCopyWindowInfo(options, kCGNullWindowID)
            if not window_list:
                return []

            for window in window_list:
                # Filter out windows without names or owners (background processes)
                owner_name = window.get(kCGWindowOwnerName)
                window_title = window.get(kCGWindowName)
                window_id = window.get(kCGWindowNumber)  # Unique window ID
                window_bounds = window.get(
                    "kCGWindowBounds"
                )  # Dict with X, Y, Width, Height

                # Apply filtering based on `all_windows`
                if not all_windows:
                    # Example filters: skip background apps, windows with no title
                    if not owner_name or owner_name in [
                        "Dock",
                        "Window Server",
                        "SystemUIServer",
                    ]:
                        continue
                    if not window_title:
                        continue
                    # Add more filters if needed (e.g., based on kCGWindowLayer == 0)

                info = {
                    "id": window_id,
                    "title": window_title or "",
                    "owner": owner_name or "",
                    "rect": (
                        (
                            window_bounds.get("X", 0),
                            window_bounds.get("Y", 0),
                            window_bounds.get("Width", 0),
                            window_bounds.get("Height", 0),
                        )
                        if window_bounds
                        else (0, 0, 0, 0)
                    ),
                    "backend": "macos_native",
                }
                windows_info.append(info)
            logger.debug(f"Found {len(windows_info)} windows via macOS Native API.")
            return windows_info
        except Exception as e:
            logger.error(f"Error listing windows using macOS Native API: {e}")
            # Fall through to pygetwindow if available

    # pygetwindow (Cross-platform fallback)
    if PYGETWINDOW_AVAILABLE and gw:
        try:
            all_gw_windows = gw.getAllWindows()
            for window in all_gw_windows:
                # Apply filtering based on `all_windows`
                if not all_windows:
                    # pygetwindow filtering is less reliable, try basic checks
                    if not window.title or not window.visible or window.isMinimized:
                        continue
                    # Add platform-specific checks if possible (e.g., check class name on Windows)

                info = {
                    "id": getattr(
                        window, "_hWnd", id(window)
                    ),  # Use hWnd on Win, fallback to object ID
                    "title": window.title or "",
                    "owner": "N/A",  # pygetwindow doesn't easily provide owner
                    "rect": (window.left, window.top, window.width, window.height),
                    "is_active": window.isActive,
                    "is_visible": window.visible,
                    "is_minimized": window.isMinimized,
                    "backend": "pygetwindow",
                }
                windows_info.append(info)
            logger.debug(f"Found {len(windows_info)} windows via pygetwindow.")
            return windows_info
        except Exception as e:
            logger.error(f"Error listing windows using pygetwindow: {e}")

    logger.error("No suitable library available for listing windows on this platform.")
    return []


def find_window(
    title_substring: Optional[str] = None,
    owner_name: Optional[str] = None,
    window_id: Optional[Any] = None,
) -> Optional[WindowObject]:
    """
    Finds a single window based on title, owner, or ID.

    Args:
        title_substring: Substring to match in the window title (case-insensitive).
        owner_name: Exact name of the owning application (macOS only).
        window_id: The unique ID of the window (platform-specific).

    Returns:
        A window object (type depends on backend) or None if not found.
        Prefers macOS Native API if available, falls back to pygetwindow.
    """
    logger.debug(
        f"Finding window by Title:'{title_substring}', Owner:'{owner_name}', ID:'{window_id}'"
    )

    # macOS Native Search
    if IS_MACOS and MACOS_NATIVE_AVAILABLE and CGWindowListCopyWindowInfo:
        try:
            options = kCGWindowListOptionOnScreenOnly  # Adjust options as needed
            window_list = CGWindowListCopyWindowInfo(options, kCGNullWindowID)
            if not window_list:
                return None

            for window_info in window_list:
                match = True
                if (
                    window_id is not None
                    and window_info.get(kCGWindowNumber) != window_id
                ):
                    match = False
                if (
                    owner_name is not None
                    and window_info.get(kCGWindowOwnerName) != owner_name
                ):
                    match = False
                if title_substring is not None:
                    title = window_info.get(kCGWindowName)
                    if not title or title_substring.lower() not in title.lower():
                        match = False

                if match:
                    # Need to get the actual NSWindow object for control actions
                    app = AppKit.NSRunningApplication.runningApplicationWithProcessIdentifier_(
                        window_info["kCGWindowOwnerPID"]
                    )
                    if app:
                        # Finding the *specific* NSWindow from CGWindow info is tricky.
                        # This finds the app, might need more work to target specific window ID.
                        # Returning the app object for now, activation works on app level.
                        logger.info(
                            f"Found matching app via macOS Native API: {app.localizedName()}"
                        )
                        # How to return something controllable? Maybe just PID or App Name?
                        # Let's return the info dict for now, control functions need to handle it.
                        return {"type": "macos_native", "info": window_info, "app": app}
            logger.debug("No matching window found via macOS Native API.")
        except Exception as e:
            logger.error(f"Error finding window via macOS Native API: {e}")
            # Fall through

    # pygetwindow Search
    if PYGETWINDOW_AVAILABLE and gw:
        try:
            # gw doesn't support owner or ID directly in search, need to iterate
            windows = gw.getAllWindows()
            title_lower = title_substring.lower() if title_substring else None

            for window in windows:
                if (
                    window_id is not None
                ):  # Check ID first if provided (Windows specific)
                    if IS_WINDOWS and getattr(window, "_hWnd", None) == window_id:
                        logger.info(f"Found window by ID (hWnd): {window_id}")
                        return window
                    # Add ID checks for other platforms if gw supports them

                if title_lower:
                    if window.title and title_lower in window.title.lower():
                        logger.info(
                            f"Found window by title substring: '{window.title}'"
                        )
                        return window
                elif (
                    window_id is None and owner_name is None
                ):  # Avoid returning first window if no criteria given
                    pass

            logger.debug("No matching window found via pygetwindow.")
            return None
        except Exception as e:
            logger.error(f"Error finding window via pygetwindow: {e}")

    return None


def activate_window(window: WindowObject) -> bool:
    """
    Brings the specified window to the foreground and activates it.

    Args:
        window: The window object (obtained from find_window or list_windows).

    Returns:
        True if activation was attempted successfully, False otherwise.
    """
    if window is None:
        logger.error("Cannot activate a None window.")
        return False

    logger.info(f"Activating window: {window}")
    backend = "unknown"

    try:
        # Handle macOS Native object (dictionary containing app reference)
        if isinstance(window, dict) and window.get("type") == "macos_native":
            backend = "macos_native"
            app = window.get("app")
            if app and hasattr(app, "activateWithOptions_"):
                # Activate the application
                success = app.activateWithOptions_(
                    AppKit.NSApplicationActivateIgnoringOtherApps
                )
                logger.info(
                    f"macOS app activation attempted for '{app.localizedName()}': {success}"
                )
                # Activating specific window ID is more complex, might need AppleScript/AXAPI
                return success
            else:
                logger.error("Invalid macOS native window object for activation.")
                return False

        # Handle pygetwindow object
        elif PYGETWINDOW_AVAILABLE and hasattr(window, "activate"):
            backend = "pygetwindow"
            # Ensure window is not minimized first (activate might fail)
            if hasattr(window, "isMinimized") and window.isMinimized:
                if hasattr(window, "restore"):
                    window.restore()
                    time.sleep(0.1)  # Give time to restore
                else:
                    logger.warning(
                        f"Window '{window.title}' is minimized but restore method unavailable."
                    )

            window.activate()
            # Check if it became active (might not work reliably across platforms)
            time.sleep(0.2)  # Allow time for activation
            # active_win = gw.getActiveWindow() if gw else None
            # success = active_win == window
            # logger.info(f"pygetwindow activation attempted for '{window.title}'. Active check: {success}")
            logger.info(f"pygetwindow activation attempted for '{window.title}'.")
            return True  # Assume success if no exception

        else:
            logger.error(
                f"Unsupported window object type for activation: {type(window)}"
            )
            return False

    except Exception as e:
        logger.error(f"Error activating window using {backend}: {e}")
        return False


def close_window(window: WindowObject) -> bool:
    """
    Closes the specified window.

    Args:
        window: The window object.

    Returns:
        True if close was attempted successfully, False otherwise.
    """
    if window is None:
        return False
    logger.info(f"Closing window: {window}")
    backend = "unknown"

    try:
        # Handle macOS Native object (needs specific window reference or AXAPI)
        if isinstance(window, dict) and window.get("type") == "macos_native":
            backend = "macos_native"
            logger.warning(
                "Closing specific macOS windows via native API requires more complex implementation (e.g., AXAPI). Attempting app termination."
            )
            # Example: Terminate the app (use with caution!)
            # app = window.get("app")
            # if app: return app.terminate()
            return False  # Placeholder

        # Handle pygetwindow object
        elif PYGETWINDOW_AVAILABLE and hasattr(window, "close"):
            backend = "pygetwindow"
            window.close()
            logger.info(
                f"pygetwindow close attempted for '{getattr(window, 'title', 'N/A')}'."
            )
            return True
        else:
            logger.error(f"Unsupported window object type for closing: {type(window)}")
            return False
    except Exception as e:
        logger.error(f"Error closing window using {backend}: {e}")
        return False


def get_window_rect(window: WindowObject) -> Optional[Tuple[int, int, int, int]]:
    """
    Gets the bounding rectangle of the specified window.

    Args:
        window: The window object.

    Returns:
        A tuple (left, top, width, height) or None on failure.
    """
    if window is None:
        return None
    logger.debug(f"Getting rect for window: {window}")
    backend = "unknown"

    try:
        # Handle macOS Native object
        if isinstance(window, dict) and window.get("type") == "macos_native":
            backend = "macos_native"
            bounds = window.get("info", {}).get("kCGWindowBounds")
            if bounds:
                return (
                    int(bounds.get("X", 0)),
                    int(bounds.get("Y", 0)),
                    int(bounds.get("Width", 0)),
                    int(bounds.get("Height", 0)),
                )
            else:
                return None

        # Handle pygetwindow object
        elif PYGETWINDOW_AVAILABLE and all(
            hasattr(window, attr) for attr in ["left", "top", "width", "height"]
        ):
            backend = "pygetwindow"
            return (window.left, window.top, window.width, window.height)
        else:
            logger.error(f"Unsupported window object type for get_rect: {type(window)}")
            return None
    except Exception as e:
        logger.error(f"Error getting window rect using {backend}: {e}")
        return None


def resize_window(window: WindowObject, width: int, height: int) -> bool:
    """
    Resizes the specified window to the given dimensions.

    Args:
        window: The window object.
        width: New width in pixels.
        height: New height in pixels.

    Returns:
        True if resize was attempted successfully, False otherwise.
    """
    if window is None:
        return False
    logger.info(f"Resizing window to {width}x{height}: {window}")
    backend = "unknown"

    try:
        # Handle macOS Native object
        if isinstance(window, dict) and window.get("type") == "macos_native":
            backend = "macos_native"
            logger.warning(
                "Resizing specific macOS windows via native API requires more complex implementation."
            )
            return False  # Placeholder - would need AXUIElement or similar

        # Handle pygetwindow object
        elif PYGETWINDOW_AVAILABLE and hasattr(window, "resizeTo"):
            backend = "pygetwindow"
            window.resizeTo(width, height)
            logger.info(
                f"pygetwindow resize attempted for '{getattr(window, 'title', 'N/A')}'."
            )
            return True
        else:
            logger.error(f"Unsupported window object type for resizing: {type(window)}")
            return False
    except Exception as e:
        logger.error(f"Error resizing window using {backend}: {e}")
        return False


def move_window(window: WindowObject, x: int, y: int) -> bool:
    """
    Moves the specified window to the given screen coordinates.

    Args:
        window: The window object.
        x: New x-coordinate for top-left corner.
        y: New y-coordinate for top-left corner.

    Returns:
        True if move was attempted successfully, False otherwise.
    """
    if window is None:
        return False
    logger.info(f"Moving window to ({x}, {y}): {window}")
    backend = "unknown"

    try:
        # Handle macOS Native object
        if isinstance(window, dict) and window.get("type") == "macos_native":
            backend = "macos_native"
            logger.warning(
                "Moving specific macOS windows via native API requires more complex implementation."
            )
            return False  # Placeholder - would need AXUIElement or similar

        # Handle pygetwindow object
        elif PYGETWINDOW_AVAILABLE and hasattr(window, "moveTo"):
            backend = "pygetwindow"
            window.moveTo(x, y)
            logger.info(
                f"pygetwindow move attempted for '{getattr(window, 'title', 'N/A')}'."
            )
            return True
        else:
            logger.error(f"Unsupported window object type for moving: {type(window)}")
            return False
    except Exception as e:
        logger.error(f"Error moving window using {backend}: {e}")
        return False


def minimize_window(window: WindowObject) -> bool:
    """
    Minimizes the specified window.

    Args:
        window: The window object.

    Returns:
        True if minimize was attempted successfully, False otherwise.
    """
    if window is None:
        return False
    logger.info(f"Minimizing window: {window}")
    backend = "unknown"

    try:
        # Handle macOS Native object
        if isinstance(window, dict) and window.get("type") == "macos_native":
            backend = "macos_native"
            app = window.get("app")
            if app and hasattr(app, "hide"):
                app.hide()
                logger.info(
                    f"macOS app minimize attempted for '{app.localizedName()}'."
                )
                return True
            return False

        # Handle pygetwindow object
        elif PYGETWINDOW_AVAILABLE and hasattr(window, "minimize"):
            backend = "pygetwindow"
            window.minimize()
            logger.info(
                f"pygetwindow minimize attempted for '{getattr(window, 'title', 'N/A')}'."
            )
            return True
        else:
            logger.error(
                f"Unsupported window object type for minimizing: {type(window)}"
            )
            return False
    except Exception as e:
        logger.error(f"Error minimizing window using {backend}: {e}")
        return False


def maximize_window(window: WindowObject) -> bool:
    """
    Maximizes the specified window.

    Args:
        window: The window object.

    Returns:
        True if maximize was attempted successfully, False otherwise.
    """
    if window is None:
        return False
    logger.info(f"Maximizing window: {window}")
    backend = "unknown"

    try:
        # Handle macOS Native object
        if isinstance(window, dict) and window.get("type") == "macos_native":
            backend = "macos_native"
            # macOS doesn't have true "maximize" - it has zoom
            app = window.get("app")
            if app and hasattr(app, "activateWithOptions_"):
                # Activate first
                app.activateWithOptions_(AppKit.NSApplicationActivateIgnoringOtherApps)
                # Would need AXUIElement for actual window zoom
                logger.warning("True window maximize not implemented for macOS.")
                return True
            return False

        # Handle pygetwindow object
        elif PYGETWINDOW_AVAILABLE and hasattr(window, "maximize"):
            backend = "pygetwindow"
            window.maximize()
            logger.info(
                f"pygetwindow maximize attempted for '{getattr(window, 'title', 'N/A')}'."
            )
            return True
        else:
            logger.error(
                f"Unsupported window object type for maximizing: {type(window)}"
            )
            return False
    except Exception as e:
        logger.error(f"Error maximizing window using {backend}: {e}")
        return False


def restore_window(window: WindowObject) -> bool:
    """
    Restores a minimized or maximized window to its previous state.

    Args:
        window: The window object.

    Returns:
        True if restore was attempted successfully, False otherwise.
    """
    if window is None:
        return False
    logger.info(f"Restoring window: {window}")
    backend = "unknown"

    try:
        # Handle macOS Native object
        if isinstance(window, dict) and window.get("type") == "macos_native":
            backend = "macos_native"
            app = window.get("app")
            if app and hasattr(app, "unhide"):
                app.unhide()
                logger.info(f"macOS app restore attempted for '{app.localizedName()}'.")
                return True
            return False

        # Handle pygetwindow object
        elif PYGETWINDOW_AVAILABLE and hasattr(window, "restore"):
            backend = "pygetwindow"
            window.restore()
            logger.info(
                f"pygetwindow restore attempted for '{getattr(window, 'title', 'N/A')}'."
            )
            return True
        else:
            logger.error(
                f"Unsupported window object type for restoring: {type(window)}"
            )
            return False
    except Exception as e:
        logger.error(f"Error restoring window using {backend}: {e}")
        return False
