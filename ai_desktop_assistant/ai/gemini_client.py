# Location: ai_desktop_assistant/ai/gemini_client.py
"""
Gemini API Client

This module provides a client for interacting with Google's Gemini model API.
"""

import logging
import asyncio
from typing import Any, Dict, List, Optional

from google import genai
from google.genai import types as genai_types

from ai_desktop_assistant.core.exceptions import APIError, ConfigurationError
from ai_desktop_assistant.core.config import AppConfig


class GeminiClient:
    """
    Client for interacting with Google's Gemini models.

    This class wraps the official google-genai SDK to provide
    a convenient interface for our application.
    """

    def __init__(self, config: "AppConfig"):
        """
        Initialize the Gemini client.

        Args:
            config: Application configuration containing API key and voice settings
        """
        self.logger = logging.getLogger(__name__)
        self.config = config
        self.api_key = config.api_key
        self.client = None
        self.live_session = None
        # Context manager for live session (for cleanup)
        self.live_session_cm = None
        # Lock to prevent concurrent send/receive on the live session
        self._send_lock = asyncio.Lock()

    async def initialize(self) -> None:
        """
        Initialize the Gemini client.

        Raises:
            ConfigurationError: If the API key is not provided
            APIError: If initialization fails
        """
        if not self.api_key:
            raise ConfigurationError("Gemini API key is required")

        try:
            # Initialize the SDK client
            self.client = genai.Client(
                api_key=self.api_key,
                http_options={"api_version": "v1beta"},  # Required for Live API
            )
            self.logger.info("Gemini client initialized successfully")
        except Exception as e:
            self.logger.error(f"Error initializing Gemini client: {e}")
            raise APIError(f"Failed to initialize Gemini client: {e}")

    async def generate_content(
        self,
        prompt: str,
        model_name: str = "gemini-2.0-flash-001",
        conversation_history: Optional[List[Dict[str, Any]]] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        """
        Generate content with the Gemini model.

        Args:
            prompt: The prompt to generate content from
            model_name: The name of the model to use
            conversation_history: Optional conversation history for context
            tools: Optional tools to make available to the model

        Returns:
            The generated content as text

        Raises:
            APIError: If content generation fails
        """
        if not self.client:
            await self.initialize()

        try:
            # Create message content
            messages = conversation_history or []

            # Add the current prompt
            messages.append({"role": "user", "parts": [{"text": prompt}]})

            # Generate content
            response = self.client.models.generate_content(
                model=model_name,
                contents=messages,
                tools=tools,
                safety_settings=None,  # Use default safety settings
            )

            # Extract and return the text
            if hasattr(response, "text"):
                return response.text
            else:
                return response.parts[0].text

        except Exception as e:
            self.logger.error(f"Error generating content: {e}")
            raise APIError(f"Failed to generate content: {e}")

    async def start_live_session(
        self,
        model_name: str = "gemini-2.0-flash-live-001",
        response_modality: str = "TEXT",
        system_instruction: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        """
        Start a live session with the Gemini model.

        Args:
            model_name: The name of the model to use
            response_modality: The modality of the response (TEXT or AUDIO)
            system_instruction: Optional system instruction for the model
            tools: Optional tools to make available to the model

        Raises:
            APIError: If session creation fails
        """
        if not self.client:
            await self.initialize()

        try:
            # Configure the session
            config = {
                "response_modalities": [response_modality],
            }

            if system_instruction:
                config["system_instruction"] = genai_types.Content(
                    parts=[genai_types.Part(text=system_instruction)]
                )

            if tools:
                config["tools"] = tools

            # Configure voice for audio responses if specified in config
            if self.config.preferred_voice:
                config["speech_config"] = genai_types.SpeechConfig(
                    voice_config=genai_types.VoiceConfig(
                        prebuilt_voice_config=genai_types.PrebuiltVoiceConfig(
                            voice_name=self.config.preferred_voice
                        )
                    )
                )
            # Create the live session context manager
            cm = self.client.aio.live.connect(model=model_name, config=config)
            # Enter context to establish the session
            self.live_session = await cm.__aenter__()
            # Store context manager for potential cleanup
            self.live_session_cm = cm
            self.logger.info(f"Started live session with model {model_name}")

        except Exception as e:
            self.logger.error(f"Error starting live session: {e}")
            raise APIError(f"Failed to start live session: {e}")

    async def send_message_to_live_session(
        self, message: str, end_of_turn: bool = True
    ) -> str:
        """
        Send a message to the live session.

        Args:
            message: The message to send
            end_of_turn: Whether this is the end of the user's turn

        Returns:
            The combined response from the model

        Raises:
            APIError: If sending the message fails
        """
        # Prevent concurrent sends/receives on the same live session
        async with self._send_lock:
            if not self.live_session:
                await self.start_live_session()

            try:
                # Send the message
                await self.live_session.send(input=message, end_of_turn=end_of_turn)

                # Collect the response
                response_text = ""
                async for response in self.live_session.receive():
                    if text := response.text:
                        response_text += text

                    # Check for tool calls (for future feature)
                    if tool_call := response.tool_call:
                        self.logger.debug(f"Tool call received: {tool_call}")
                        # TODO: Handle tool calls when implementing actions

                return response_text

            except Exception as e:
                self.logger.error(f"Error sending message to live session: {e}")
                raise APIError(f"Failed to send message to live session: {e}")

    async def close_live_session(self) -> None:
        """
        Close the live session.

        Raises:
            APIError: If closing the session fails
        """
        if not self.live_session:
            return

        try:
            await self.live_session.close()
            self.live_session = None
            self.logger.info("Closed live session")
        except Exception as e:
            self.logger.error(f"Error closing live session: {e}")
            raise APIError(f"Failed to close live session: {e}")
