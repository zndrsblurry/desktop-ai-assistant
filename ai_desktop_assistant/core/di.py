# Location: ai_desktop_assistant/core/di.py
"""
Dependency Injection Container

This module implements a simple dependency injection container
for managing service dependencies.
"""

import inspect
import logging
from typing import Any, Callable, Dict, Optional, Type, TypeVar, get_type_hints

T = TypeVar("T")


class DependencyContainer:
    """
    Simple dependency injection container.

    This container manages service dependencies and provides
    a way to resolve dependencies at runtime.
    """

    def __init__(self):
        """Initialize the dependency container."""
        self.logger = logging.getLogger(__name__)
        self._instances: Dict[Type, Any] = {}
        self._factories: Dict[Type, Callable[..., Any]] = {}

    def register_instance(
        self, instance: Any, interface: Optional[Type] = None
    ) -> None:
        """
        Register an instance with the container.

        Args:
            instance: The instance to register
            interface: Optional interface type to register the instance as
        """
        if interface is None:
            interface = type(instance)

        self._instances[interface] = instance
        self.logger.debug(f"Registered instance of {interface.__name__}")

    def register_factory(self, interface: Type[T], factory: Callable[..., T]) -> None:
        """
        Register a factory function for creating instances.

        Args:
            interface: The interface type to register
            factory: Factory function that creates instances of the interface
        """
        self._factories[interface] = factory
        self.logger.debug(f"Registered factory for {interface.__name__}")

    def register_type(self, interface: Type[T], implementation: Type[T]) -> None:
        """
        Register a type implementation.

        Args:
            interface: The interface type to register
            implementation: The implementation type
        """

        def factory():
            # Resolve constructor dependencies
            constructor = implementation.__init__
            if constructor is object.__init__:
                # No custom constructor, just instantiate
                return implementation()

            # Get constructor parameters
            sig = inspect.signature(constructor)
            params = {}

            for name, param in sig.parameters.items():
                if name == "self":
                    continue

                # Get parameter type hint
                type_hints = get_type_hints(constructor)
                param_type = type_hints.get(name, Any)

                # Resolve parameter dependency
                if param_type != Any:
                    params[name] = self.resolve(param_type)

            return implementation(**params)

        self._factories[interface] = factory
        self.logger.debug(
            f"Registered type {implementation.__name__} for {interface.__name__}"
        )

    def resolve(self, interface: Type[T]) -> T:
        """
        Resolve a dependency by interface type.

        Args:
            interface: The interface type to resolve

        Returns:
            An instance of the requested interface

        Raises:
            KeyError: If the interface is not registered
        """
        # Check if we have a cached instance
        if interface in self._instances:
            return self._instances[interface]

        # Check if we have a factory
        if interface in self._factories:
            instance = self._factories[interface]()
            self._instances[interface] = instance  # Cache the instance
            return instance

        # If the interface is a concrete class, try to instantiate it
        if not inspect.isabstract(interface):
            try:
                instance = interface()
                self._instances[interface] = instance
                return instance
            except Exception as e:
                self.logger.error(f"Error instantiating {interface.__name__}: {e}")

        raise KeyError(f"No registration found for {interface.__name__}")
