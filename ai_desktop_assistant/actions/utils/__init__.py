# """
# Action Utilities Module

# This module provides utility functions and classes commonly used by
# action executors and command definitions.

# Examples:
# - Screen interaction utilities (capture, finding elements via vision)
# - Window management utilities (finding, activating, closing windows)
# - Platform-specific helpers
# - Vision utilities (OCR, template matching - if using OpenCV directly)
# """

# # Import specific utility classes or functions
# from .screen import (
#     capture_screen_mss,
#     get_monitor_info,
#     find_window_by_title,  # Example
#     get_active_window_title,  # Example
# )
# from .vision import (
#     find_template_on_screen,  # Example using OpenCV
#     extract_text_from_image,  # Example using an OCR library
# )
# from .window import (  # This might overlap/replace parts of screen.py
#     activate_window,
#     close_window,
#     list_windows,
#     get_window_rect,
# )


# # Export key utilities
# __all__ = [
#     "capture_screen_mss",
#     "get_monitor_info",
#     "find_window_by_title",
#     "get_active_window_title",
#     "find_template_on_screen",
#     "extract_text_from_image",
#     "activate_window",
#     "close_window",
#     "list_windows",
#     "get_window_rect",
# ]

# # Constants related to utilities
# UTIL_CONSTANTS = {
#     "DEFAULT_OCR_LANGUAGE": "eng",
#     "DEFAULT_TEMPLATE_MATCHING_THRESHOLD": 0.8,
#     "WINDOW_ENUMERATION_TIMEOUT": 2.0,  # Seconds
# }
