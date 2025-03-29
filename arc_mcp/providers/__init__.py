"""Provider handlers for Arc MCP."""

import logging
from typing import Dict, List, Optional

from arc_mcp.providers.base import ProviderHandler
from arc_mcp.providers.netlify import NetlifyProviderHandler
from arc_mcp.providers.vercel import VercelProviderHandler
from arc_mcp.providers.shared_hosting import SharedHostingProviderHandler
from arc_mcp.providers.hostm import HostmProviderHandler

logger = logging.getLogger("arc-mcp.providers")

# Registry of provider handlers
_PROVIDER_HANDLERS = {
    "netlify": NetlifyProviderHandler(),
    "vercel": VercelProviderHandler(),
    "shared-hosting": SharedHostingProviderHandler(),
    "hostm": HostmProviderHandler(),
}

def get_provider_handler(provider_type: str) -> ProviderHandler:
    """Get the appropriate provider handler for a provider type.
    
    Args:
        provider_type: The type of provider
        
    Returns:
        A provider handler instance
        
    Raises:
        ValueError: If the provider type is not supported
    """
    handler = _PROVIDER_HANDLERS.get(provider_type.lower())
    if not handler:
        supported = ", ".join(_PROVIDER_HANDLERS.keys())
        raise ValueError(f"Unsupported provider: {provider_type}. Supported providers: {supported}")
    return handler

def list_supported_providers() -> List[str]:
    """Get a list of supported provider types.
    
    Returns:
        List of supported provider types
    """
    return list(_PROVIDER_HANDLERS.keys())