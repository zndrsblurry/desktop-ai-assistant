"""
Tool Registry for AI Desktop Assistant

Manages tool definitions, providing methods to register tools and retrieve
their schemas in formats suitable for AI models like Gemini (Function Calling)
and potentially LangChain.
"""

import logging
import inspect
from typing import Dict, List, Any, Optional, Callable, Type

# Use Pydantic for defining structured arguments, crucial for function calling schemas
try:
    from pydantic import BaseModel, Field
    from pydantic.json_schema import GenerateJsonSchema  # For generating schema

    PYDANTIC_AVAILABLE = True
except ImportError:
    logging.error(
        "Pydantic v2 is required for tool schema generation. Install with: pip install pydantic"
    )

    # Define placeholder types for type checking
    class BaseModel:
        pass

    def Field(*args, **kwargs):
        return None

    class GenerateJsonSchema:
        pass  # Dummy

    PYDANTIC_AVAILABLE = False


# Google Generative AI types for FunctionDeclaration
try:
    from google import genai
    from google.genai.types import FunctionDeclaration, Tool, Schema, Type as GoogleType

    GOOGLE_SDK_AVAILABLE = True

    # Mapping from Pydantic/JSON Schema types to Google API types
    # Based on Google's documentation/examples for function calling
    TYPE_MAP = {
        "string": GoogleType.STRING,
        "integer": GoogleType.INTEGER,
        "number": GoogleType.NUMBER,  # Floats map to NUMBER
        "boolean": GoogleType.BOOLEAN,
        "array": GoogleType.ARRAY,
        "object": GoogleType.OBJECT,
        # Note: 'null' is not directly mapped, handled via 'nullable' or optional fields
    }

except ImportError:
    logging.warning(
        "Google Generative AI SDK not found. Cannot generate Google FunctionDeclarations."
    )
    GOOGLE_SDK_AVAILABLE = False
    # Dummy types
    FunctionDeclaration = Any
    Tool = Any
    Schema = Any
    GoogleType = Any
    TYPE_MAP = {}


# LangChain Tool types (optional, if providing tools to LangChain Agent)
try:
    from langchain_core.tools import BaseTool as LangChainBaseTool
    from langchain_core.tools import Tool as LangChainTool

    LANGCHAIN_AVAILABLE = True
except ImportError:
    logging.debug("LangChain core not found. LangChain tool generation disabled.")
    LangChainBaseTool = object  # Dummy
    LangChainTool = object  # Dummy
    LANGCHAIN_AVAILABLE = False


logger = logging.getLogger(__name__)


class CustomJsonSchemaGenerator(GenerateJsonSchema):
    """Custom schema generator if specific modifications are needed."""

    # Override methods here if needed, e.g., to handle specific types
    pass


class ToolRegistry:
    """
    Registry for AI tools that can be used for function calling with
    models like Gemini or LangChain agents.
    """

    def __init__(self):
        """Initialize the tool registry with empty dictionaries."""
        # Global registry storing raw function definitions and metadata
        self._tool_definitions: Dict[str, Dict[str, Any]] = {}
        # Cache for generated Google FunctionDeclarations
        self._google_declaration_cache: Dict[str, Optional[FunctionDeclaration]] = {}
        # Cache for generated LangChain Tool objects
        self._langchain_tool_cache: Dict[str, Optional[LangChainBaseTool]] = {}

    def register_tool(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        category: str = "general",
        enabled: bool = True,
        args_schema: Optional[Type[BaseModel]] = None,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """
        Decorator to register a function as an available tool.

        Args:
            name: Name for the tool (must be unique). Defaults to function name.
            description: Clear description of what the tool does (for the AI).
                        Defaults to function docstring. Crucial for function calling.
            category: Category for organizing tools (e.g., 'mouse', 'system').
            enabled: Whether the tool is enabled by default.
            args_schema: Pydantic model defining the expected arguments. Required if
                        the function takes arguments relevant to the AI.

        Returns:
            Decorator function that registers the tool definition.
        """
        if not PYDANTIC_AVAILABLE:
            raise ImportError(
                "Pydantic must be installed to register tools with argument schemas."
            )

        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            nonlocal name, description
            tool_name = name or func.__name__

            # Basic check for valid function name characters (alphanumeric + underscore)
            if not tool_name.replace("_", "").isalnum():
                logger.error(
                    f"Tool name '{tool_name}' contains invalid characters. Use only letters, numbers, and underscores."
                )
                # Decide whether to raise an error or just warn
                return func  # Skip registration

            if tool_name in self._tool_definitions:
                logger.warning(
                    f"Tool '{tool_name}' is already registered. Overwriting definition."
                )

            # Use function docstring for description if not provided
            if description is None:
                if func.__doc__:
                    description = inspect.cleandoc(func.__doc__)
                else:
                    description = f"No description provided for tool '{tool_name}'."
                    logger.warning(description)
            if not description:  # Ensure description is not empty
                logger.error(
                    f"Tool '{tool_name}' must have a non-empty description for AI function calling."
                )
                return func  # Skip registration

            is_async = inspect.iscoroutinefunction(func)

            # Validate args_schema if provided
            if args_schema and not issubclass(args_schema, BaseModel):
                logger.error(
                    f"Tool '{tool_name}': args_schema must be a Pydantic BaseModel subclass, got {type(args_schema)}."
                )
                return func  # Skip registration

            self._tool_definitions[tool_name] = {
                "function": func,
                "description": description,
                "category": category,
                "enabled": enabled,
                "is_async": is_async,
                "args_schema": args_schema,
                "name": tool_name,
            }
            # Invalidate caches for this tool
            self._google_declaration_cache.pop(tool_name, None)
            self._langchain_tool_cache.pop(tool_name, None)

            logger.debug(
                f"Registered tool definition: '{tool_name}' (Async: {is_async}, Category: {category})"
            )
            return func

        return decorator

    def get_tool_definition(self, name: str) -> Optional[Dict[str, Any]]:
        """Get the raw definition dictionary of a tool by name."""
        return self._tool_definitions.get(name)

    def _generate_google_schema(self, args_schema: Type[BaseModel]) -> Optional[Schema]:
        """Generates a Google API Schema object from a Pydantic model."""
        if not GOOGLE_SDK_AVAILABLE or not PYDANTIC_AVAILABLE:
            return None
        try:
            # Generate JSON Schema from Pydantic model
            # Use Pydantic's v2 model_json_schema()
            # json_schema = args_schema.model_json_schema(schema_generator=CustomJsonSchemaGenerator)
            # Pydantic v1 compatibility:
            json_schema = args_schema.schema(schema_generator=CustomJsonSchemaGenerator)

            # Basic conversion from JSON Schema to Google API Schema
            # This might need refinement based on complex types (enums, nested objects, etc.)
            google_properties = {}
            required_params = json_schema.get("required", [])

            for prop_name, prop_schema in json_schema.get("properties", {}).items():
                prop_type = prop_schema.get("type")
                google_type = TYPE_MAP.get(prop_type, GoogleType.TYPE_UNSPECIFIED)
                if google_type == GoogleType.TYPE_UNSPECIFIED:
                    logger.warning(
                        f"Cannot map JSON schema type '{prop_type}' to Google Type for property '{prop_name}' in schema '{args_schema.__name__}'."
                    )
                    # Skip property or handle as string? For now, skip.
                    continue

                # Handle arrays (needs item type)
                items_schema = None
                if google_type == GoogleType.ARRAY:
                    item_type_schema = prop_schema.get("items", {})
                    item_type = item_type_schema.get("type")
                    google_item_type = TYPE_MAP.get(item_type)
                    if google_item_type:
                        items_schema = Schema(type=google_item_type)
                    else:
                        logger.warning(
                            f"Cannot map array item type '{item_type}' for property '{prop_name}'."
                        )
                        continue  # Skip array if item type unknown

                google_properties[prop_name] = Schema(
                    type=google_type,
                    description=prop_schema.get("description", ""),
                    nullable=prop_name not in required_params,  # Basic nullable check
                    items=items_schema,  # Add items schema for arrays
                    # Add format, enum handling if needed
                )

            return Schema(
                type=GoogleType.OBJECT,
                properties=google_properties,
                required=required_params,
            )

        except Exception as e:
            logger.exception(
                f"Error generating Google Schema for Pydantic model {args_schema.__name__}: {e}"
            )
            return None

    def _create_google_function_declaration(
        self, definition: Dict[str, Any]
    ) -> Optional[FunctionDeclaration]:
        """Creates a Google API FunctionDeclaration from a tool definition."""
        tool_name = definition["name"]
        if not GOOGLE_SDK_AVAILABLE:
            return None

        if tool_name in self._google_declaration_cache:
            return self._google_declaration_cache[tool_name]

        args_schema = definition["args_schema"]
        parameters_schema: Optional[Schema] = None

        if args_schema:
            parameters_schema = self._generate_google_schema(args_schema)
            if not parameters_schema:
                logger.error(
                    f"Failed to generate parameter schema for tool '{tool_name}'. Cannot create declaration."
                )
                self._google_declaration_cache[tool_name] = None  # Cache failure
                return None

        try:
            declaration = FunctionDeclaration(
                name=tool_name,
                description=definition["description"],
                parameters=parameters_schema,
            )
            self._google_declaration_cache[tool_name] = declaration
            return declaration
        except Exception as e:
            logger.exception(
                f"Error creating Google FunctionDeclaration for '{tool_name}': {e}"
            )
            self._google_declaration_cache[tool_name] = None
            return None

    def get_google_tool_declarations(
        self, category: Optional[str] = None, include_disabled: bool = False
    ) -> List[FunctionDeclaration]:
        """
        Gets a list of Google FunctionDeclarations for available tools.

        This is used to configure the Gemini API for function calling.

        Args:
            category: Optional category to filter by.
            include_disabled: Whether to include declarations for disabled tools.

        Returns:
            List of FunctionDeclaration objects.
        """
        if not GOOGLE_SDK_AVAILABLE:
            logger.error(
                "Cannot get Google Tool Declarations: google-generativeai SDK not available."
            )
            return []

        declarations: List[FunctionDeclaration] = []
        for definition in self._tool_definitions.values():
            if category and definition["category"] != category:
                continue
            if not include_disabled and not definition["enabled"]:
                continue

            declaration = self._create_google_function_declaration(definition)
            if declaration:
                declarations.append(declaration)

        logger.debug(
            f"Retrieved {len(declarations)} Google FunctionDeclarations (Category: {category or 'All'}, Disabled included: {include_disabled})"
        )
        return declarations

    def _create_langchain_tool(
        self, definition: Dict[str, Any]
    ) -> Optional[LangChainBaseTool]:
        """Creates a LangChain Tool object from a tool definition."""
        tool_name = definition["name"]
        if not LANGCHAIN_AVAILABLE:
            return None

        if tool_name in self._langchain_tool_cache:
            return self._langchain_tool_cache[tool_name]

        func = definition["function"]
        is_async = definition["is_async"]
        args_schema = definition["args_schema"]

        try:
            # Use LangChain's Tool class
            lc_tool = LangChainTool(
                name=tool_name,
                description=definition["description"],
                func=func if not is_async else None,
                coroutine=func if is_async else None,
                args_schema=args_schema,  # Pass Pydantic model directly if using LCEL/structured agents
            )
            self._langchain_tool_cache[tool_name] = lc_tool
            return lc_tool
        except Exception as e:
            logger.exception(
                f"Error creating LangChain Tool object for '{tool_name}': {e}"
            )
            self._langchain_tool_cache[tool_name] = None
            return None

    def get_langchain_tools(
        self, category: Optional[str] = None, include_disabled: bool = False
    ) -> List[LangChainBaseTool]:
        """
        Gets available LangChain Tool objects, optionally filtered by category.

        Args:
            category: Optional category to filter by.
            include_disabled: Whether to include disabled tools.

        Returns:
            List of available LangChain BaseTool instances.
        """
        if not LANGCHAIN_AVAILABLE:
            logger.error(
                "Cannot get LangChain Tools: langchain-core library not available."
            )
            return []

        tools: List[LangChainBaseTool] = []
        for definition in self._tool_definitions.values():
            if category and definition["category"] != category:
                continue
            if not include_disabled and not definition["enabled"]:
                continue

            tool_instance = self._create_langchain_tool(definition)
            if tool_instance:
                tools.append(tool_instance)

        logger.debug(
            f"Retrieved {len(tools)} LangChain tools (Category: {category or 'All'}, Disabled included: {include_disabled})"
        )
        return tools

    def get_tool_function(self, name: str) -> Optional[Callable]:
        """Get the underlying function for a tool by name (if enabled)."""
        definition = self.get_tool_definition(name)
        if definition and definition["enabled"]:
            return definition["function"]
        return None

    def get_tool_categories(self) -> Dict[str, List[str]]:
        """Get all tool categories and the names of tools within them."""
        categories: Dict[str, List[str]] = {}
        for name, definition in self._tool_definitions.items():
            cat = definition["category"]
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(name)
        # Sort tools within categories for consistent output
        for cat in categories:
            categories[cat].sort()
        return categories

    def enable_tool(self, name: str) -> bool:
        """Enable a tool by name."""
        definition = self.get_tool_definition(name)
        if definition:
            if not definition["enabled"]:
                definition["enabled"] = True
                # Invalidate caches
                self._google_declaration_cache.pop(name, None)
                self._langchain_tool_cache.pop(name, None)
                logger.info(f"Enabled tool '{name}'")
                return True
            else:
                logger.debug(f"Tool '{name}' is already enabled.")
                return True
        else:
            logger.warning(f"Attempted to enable non-existent tool '{name}'")
            return False

    def disable_tool(self, name: str) -> bool:
        """Disable a tool by name."""
        definition = self.get_tool_definition(name)
        if definition:
            if definition["enabled"]:
                definition["enabled"] = False
                # Invalidate caches
                self._google_declaration_cache.pop(name, None)
                self._langchain_tool_cache.pop(name, None)
                logger.info(f"Disabled tool '{name}'")
                return True
            else:
                logger.debug(f"Tool '{name}' is already disabled.")
                return True
        else:
            logger.warning(f"Attempted to disable non-existent tool '{name}'")
            return False

    def reset_registry(self) -> None:
        """Reset the tool registry and caches (primarily for testing)."""
        self._tool_definitions.clear()
        self._google_declaration_cache.clear()
        self._langchain_tool_cache.clear()
        logger.info("Tool registry has been reset.")


# Create a module-level instance for backward compatibility with function-based approach
_registry = ToolRegistry()


# Export module-level functions that delegate to the singleton instance
def register_tool(*args, **kwargs):
    return _registry.register_tool(*args, **kwargs)


def get_tool_definition(name: str) -> Optional[Dict[str, Any]]:
    return _registry.get_tool_definition(name)


def get_google_tool_declarations(*args, **kwargs):
    return _registry.get_google_tool_declarations(*args, **kwargs)


def get_langchain_tools(*args, **kwargs):
    return _registry.get_langchain_tools(*args, **kwargs)


def get_tool_function(name: str) -> Optional[Callable]:
    return _registry.get_tool_function(name)


def get_tool_categories() -> Dict[str, List[str]]:
    return _registry.get_tool_categories()


def enable_tool(name: str) -> bool:
    return _registry.enable_tool(name)


def disable_tool(name: str) -> bool:
    return _registry.disable_tool(name)


def reset_registry() -> None:
    return _registry.reset_registry()
