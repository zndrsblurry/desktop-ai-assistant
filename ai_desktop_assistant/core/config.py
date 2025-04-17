# Location: ai_desktop_assistant/core/config.py
"""
Configuration Management

This module handles loading and accessing application configuration.
"""

import json
import logging
import os
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class AppConfig:
    """Application configuration class."""

    # Application information
    app_name: str = "AI Desktop Assistant"
    version: str = "0.1.0"
    app_version: str = "0.1.0"

    # API keys and authentication
    api_key: str = "AIzaSyDKtA9ODOo6rpfTJqQBonxurEvIxbzbZc0"

    # AI model settings
    default_model: str = "gemini-2.0-flash-live-preview-04-09"
    system_prompt: str = (
        "You are a helpful AI desktop assistant that can help the user with various tasks on their computer."
    )

    # Voice settings
    voice_enabled: bool = True
    preferred_voice: str = "Kore"  # One of the available Gemini voices
    speech_rate: float = 1.0

    # UI settings
    theme: str = "dark"
    floating_mode: bool = False
    accent_color: str = "#00B8D4"  # Cyan accent color

    # Other settings
    log_level: str = "INFO"
    telemetry_enabled: bool = False

    # Extra configurations
    extra: Dict[str, Any] = field(default_factory=dict)


def load_config() -> AppConfig:
    """
    Load application configuration from environment variables and config files.

    Returns:
        AppConfig object with loaded configuration
    """
    logger = logging.getLogger(__name__)

    # Create default config
    config = AppConfig()

    # Load from config file if it exists
    config_file = os.environ.get("AI_ASSISTANT_CONFIG", "")
    if config_file and os.path.exists(config_file):
        try:
            with open(config_file, "r") as f:
                config_data = json.load(f)
                for key, value in config_data.items():
                    if hasattr(config, key):
                        setattr(config, key, value)
                    else:
                        config.extra[key] = value
            logger.info(f"Loaded configuration from {config_file}")
        except Exception as e:
            logger.error(f"Error loading config file: {e}")

    # Override with environment variables
    if api_key := os.environ.get("GOOGLE_API_KEY"):
        print(f"api_key: {api_key}")
        config.api_key = api_key

    if model := os.environ.get("AI_ASSISTANT_MODEL"):
        config.default_model = model

    if theme := os.environ.get("AI_ASSISTANT_THEME"):
        config.theme = theme

    if log_level := os.environ.get("AI_ASSISTANT_LOG_LEVEL"):
        config.log_level = log_level

    # Check for required config
    if not config.api_key:
        logger.warning(
            "API key not set. Please set GOOGLE_API_KEY environment variable or configure in config file."
        )

    return config


def save_config(config: AppConfig, path: Optional[str] = None) -> bool:
    """
    Save configuration to a JSON file.

    Args:
        config: The configuration to save
        path: Path to save the config file (optional)

    Returns:
        True if saved successfully, False otherwise
    """
    logger = logging.getLogger(__name__)

    if not path:
        path = os.environ.get("AI_ASSISTANT_CONFIG", "")
        if not path:
            user_config_dir = os.path.join(
                os.path.expanduser("~"), ".config", "ai-desktop-assistant"
            )
            os.makedirs(user_config_dir, exist_ok=True)
            path = os.path.join(user_config_dir, "config.json")

    try:
        # Convert dataclass to dict, excluding methods and private attributes
        config_dict = {
            key: getattr(config, key)
            for key in config.__dataclass_fields__
            if not key.startswith("_") and key != "extra"
        }

        # Add extra config
        config_dict.update(config.extra)

        # Write to file
        with open(path, "w") as f:
            json.dump(config_dict, f, indent=2)

        logger.info(f"Configuration saved to {path}")
        return True
    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        return False
