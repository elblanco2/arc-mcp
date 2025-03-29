"""Main server implementation for Arc MCP."""

import argparse
import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Union

try:
    from mcp import (
        ConnectionInterface, 
        MCPServer, 
        ToolExecutionError,
        PromptTemplate, 
        Resource,
        ResourceMetadata
    )
except ImportError:
    print("MCP SDK not found. Please install with 'pip install mcp-sdk'")
    sys.exit(1)

from arc_mcp.credentials import CredentialsManager
from arc_mcp.frameworks import get_framework_handler
from arc_mcp.providers import get_provider_handler

logger = logging.getLogger("arc-mcp")

class ArcMCPServer(MCPServer):
    """Arc MCP Server for deploying web applications to various hosting providers."""
    
    def __init__(self, credentials_path: Optional[str] = None, debug: bool = False):
        super().__init__()
        
        # Configure logging
        log_level = logging.DEBUG if debug else logging.INFO
        logging.basicConfig(level=log_level, 
                           format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        # Initialize credentials manager
        self.credentials_manager = CredentialsManager(
            storage_path=credentials_path or os.environ.get("SECURE_STORAGE_PATH", "~/.arc/credentials")
        )
        
        # Register capabilities
        self._register_tools()
        self._register_prompts()
        self._register_resources()
        
        logger.info("Arc MCP Server initialized")
