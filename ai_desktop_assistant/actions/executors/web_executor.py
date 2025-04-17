# Location: ai_desktop_assistant/actions/executors/web_executor.py
"""
Web Executor

This module implements the web action executor for web operations.
"""

import logging
from typing import Any, Dict, Optional, Set

import aiohttp

from ai_desktop_assistant.core.events import EventBus
from ai_desktop_assistant.core.exceptions import ActionError
from ai_desktop_assistant.interfaces.action_executor import ActionExecutor


class WebExecutor(ActionExecutor):
    """Implementation of the web action executor."""

    # Set of supported action types
    SUPPORTED_ACTIONS: Set[str] = {"web_search", "web_get", "web_post"}

    def __init__(self, event_bus: EventBus):
        """
        Initialize the web executor.

        Args:
            event_bus: The application event bus
        """
        self.logger = logging.getLogger(__name__)
        self.event_bus = event_bus
        self.session = None

    async def initialize(self) -> None:
        """Initialize the web executor."""
        self.logger.info("Initializing web executor")
        self.session = aiohttp.ClientSession()
        self.logger.info("Web executor initialized")

    async def shutdown(self) -> None:
        """Shut down the web executor."""
        self.logger.info("Shutting down web executor")
        if self.session:
            await self.session.close()
            self.session = None
        self.logger.info("Web executor shut down")

    async def execute_action(
        self, action_type: str, params: Dict[str, Any]
    ) -> Optional[Any]:
        """
        Execute a web action.

        Args:
            action_type: The type of action to execute
            params: Action parameters

        Returns:
            The action result or None if the action doesn't produce a result

        Raises:
            ActionError: If execution fails
        """
        if not self.can_execute(action_type):
            raise ActionError(f"Unsupported action type: {action_type}")

        # Ensure session is initialized
        if not self.session:
            await self.initialize()

        try:
            if action_type == "web_search":
                return await self._web_search(params)
            elif action_type == "web_get":
                return await self._web_get(params)
            elif action_type == "web_post":
                return await self._web_post(params)

            return None

        except Exception as e:
            self.logger.error(f"Error executing web action {action_type}: {e}")
            raise ActionError(f"Failed to execute web action {action_type}: {e}")

    def can_execute(self, action_type: str) -> bool:
        """
        Check if this executor can execute the given action type.

        Args:
            action_type: The action type to check

        Returns:
            True if this executor can execute the action, False otherwise
        """
        return action_type in self.SUPPORTED_ACTIONS

    async def _web_search(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform a web search.

        Args:
            params: Action parameters
                query: The search query
                search_engine: The search engine to use (optional)
                num_results: The number of results to return (optional)

        Returns:
            Dictionary with search results
        """
        # Get parameters
        query = params.get("query")
        search_engine = params.get("search_engine", "google")
        num_results = params.get("num_results", 5)

        # Validate parameters
        if query is None:
            raise ActionError("Missing required parameter: query")

        # In a real implementation, this would call a search API
        # For now, we'll return a placeholder

        return {
            "query": query,
            "search_engine": search_engine,
            "results": [
                {
                    "title": f"Search result {i + 1} for {query}",
                    "url": f"https://example.com/result{i + 1}",
                    "snippet": f"This is a snippet for search result {i + 1}.",
                }
                for i in range(num_results)
            ],
        }

    async def _web_get(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform an HTTP GET request.

        Args:
            params: Action parameters
                url: The URL to request
                headers: Optional headers to include

        Returns:
            Dictionary with response data
        """
        # Get parameters
        url = params.get("url")
        headers = params.get("headers", {})

        # Validate parameters
        if url is None:
            raise ActionError("Missing required parameter: url")

        try:
            # Make the request
            async with self.session.get(url, headers=headers) as response:
                status = response.status
                content_type = response.content_type

                if content_type == "application/json":
                    data = await response.json()
                else:
                    data = await response.text()

                return {"status": status, "content_type": content_type, "data": data}

        except aiohttp.ClientError as e:
            self.logger.error(f"HTTP request error: {e}")
            raise ActionError(f"Failed to perform HTTP GET request: {e}")

    async def _web_post(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform an HTTP POST request.

        Args:
            params: Action parameters
                url: The URL to request
                data: The data to send
                headers: Optional headers to include

        Returns:
            Dictionary with response data
        """
        # Get parameters
        url = params.get("url")
        data = params.get("data", {})
        headers = params.get("headers", {})

        # Validate parameters
        if url is None:
            raise ActionError("Missing required parameter: url")

        try:
            # Make the request
            async with self.session.post(url, json=data, headers=headers) as response:
                status = response.status
                content_type = response.content_type

                if content_type == "application/json":
                    data = await response.json()
                else:
                    data = await response.text()

                return {"status": status, "content_type": content_type, "data": data}

        except aiohttp.ClientError as e:
            self.logger.error(f"HTTP request error: {e}")
            raise ActionError(f"Failed to perform HTTP POST request: {e}")
