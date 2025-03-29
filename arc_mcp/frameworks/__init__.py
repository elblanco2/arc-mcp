"""Framework handlers for Arc MCP."""

import logging
from typing import Dict, List, Optional

from arc_mcp.frameworks.base import FrameworkHandler
from arc_mcp.frameworks.wasp import WaspFrameworkHandler
# Import other framework handlers here as they are implemented
# from arc_mcp.frameworks.nextjs import NextJSFrameworkHandler
# from arc_mcp.frameworks.astro import AstroFrameworkHandler

logger = logging.getLogger("arc-mcp.frameworks")

# Registry of framework handlers
_FRAMEWORK_HANDLERS = {
    "wasp": WaspFrameworkHandler(),
    # Add other frameworks as they are implemented
    # "nextjs": NextJSFrameworkHandler(),
    # "astro": AstroFrameworkHandler(),
}

def get_framework_handler(framework_type: str) -> FrameworkHandler:
    """Get the appropriate framework handler for a framework type.
    
    Args:
        framework_type: The type of framework
        
    Returns:
        A framework handler instance
        
    Raises:
        ValueError: If the framework type is not supported
    """
    handler = _FRAMEWORK_HANDLERS.get(framework_type.lower())
    if not handler:
        supported = ", ".join(_FRAMEWORK_HANDLERS.keys())
        raise ValueError(f"Unsupported framework: {framework_type}. Supported frameworks: {supported}")
    return handler

def list_supported_frameworks() -> List[str]:
    """Get a list of supported framework types.
    
    Returns:
        List of supported framework types
    """
    return list(_FRAMEWORK_HANDLERS.keys())
