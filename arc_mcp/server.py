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

    def _register_tools(self):
        """Register all tools provided by the server."""
        # Credential management tools
        self.register_tool(
            "save_credentials",
            self._save_credentials,
            {
                "description": "Save credentials for a provider",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "provider": {
                            "type": "string",
                            "title": "Provider"
                        },
                        "credentials": {
                            "type": "object",
                            "title": "Credentials",
                            "additionalProperties": {
                                "type": "string"
                            }
                        }
                    },
                    "required": ["provider", "credentials"]
                }
            }
        )
        
        self.register_tool(
            "validate_credentials",
            self._validate_credentials,
            {
                "description": "Validate credentials for a provider by calling their API",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "provider": {
                            "type": "string",
                            "title": "Provider"
                        },
                        "credentials": {
                            "type": "object",
                            "title": "Credentials",
                            "additionalProperties": {
                                "type": "string"
                            }
                        }
                    },
                    "required": ["provider", "credentials"]
                }
            }
        )
        
        # Deployment tools
        self.register_tool(
            "deploy_project",
            self._deploy_project,
            {
                "description": "Deploy a project to the specified provider",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "title": "Path"
                        },
                        "provider": {
                            "type": "string",
                            "title": "Provider"
                        },
                        "options": {
                            "type": "object",
                            "title": "Options",
                            "additionalProperties": True
                        }
                    },
                    "required": ["path", "provider", "options"]
                }
            }
        )
        
        # Troubleshooting tools
        self.register_tool(
            "troubleshoot_deployment",
            self._troubleshoot_deployment,
            {
                "description": "Analyze deployment logs and provide troubleshooting guidance",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "title": "Path"
                        },
                        "logs": {
                            "type": "string",
                            "title": "Logs"
                        },
                        "provider": {
                            "type": "string",
                            "title": "Provider"
                        }
                    },
                    "required": ["path", "logs", "provider"]
                }
            }
        )
        
        # Windsurf integration
        self.register_tool(
            "open_in_windsurf",
            self._open_in_windsurf,
            {
                "description": "Open a project in Windsurf (Codeium's VS Code)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "title": "Path"
                        }
                    },
                    "required": ["path"]
                }
            }
        )

    def _register_prompts(self):
        """Register all prompts provided by the server."""
        # Framework-specific deployment prompts
        self.register_prompt_template(
            "deploy-wasp",
            PromptTemplate(
                template="""
                I'll help you deploy your Wasp application.
                
                Here's what we need to do:
                
                1. First, let's verify your Wasp project at {project_path}
                2. Choose a hosting provider ({available_providers})
                3. Configure your deployment settings
                4. Deploy your application
                
                Let's start by examining your project structure to make sure everything is set up correctly.
                """,
                parameters={
                    "type": "object",
                    "properties": {
                        "project_path": {
                            "type": "string",
                            "description": "Path to your Wasp project"
                        },
                        "available_providers": {
                            "type": "string",
                            "description": "Comma-separated list of available providers"
                        }
                    },
                    "required": ["project_path"]
                }
            )
        )
        
        # Troubleshooting prompts
        self.register_prompt_template(
            "deployment-troubleshoot",
            PromptTemplate(
                template="""
                I see you're having trouble with your deployment. Let's troubleshoot this together.
                
                Your project: {project_path}
                Provider: {provider}
                
                First, I'll examine the deployment logs to identify the issue.
                Then, I'll suggest specific steps to resolve the problem.
                
                Let's start by analyzing what went wrong.
                """,
                parameters={
                    "type": "object",
                    "properties": {
                        "project_path": {
                            "type": "string",
                            "description": "Path to your project"
                        },
                        "provider": {
                            "type": "string",
                            "description": "Hosting provider name"
                        }
                    },
                    "required": ["project_path", "provider"]
                }
            )
        )
        
        # Windsurf handoff prompt
        self.register_prompt_template(
            "windsurf-handoff",
            PromptTemplate(
                template="""
                Now that your application is deployed, you can continue development in Windsurf (Codeium's VS Code).
                
                I'll help you set up Windsurf for your project at {project_path}.
                
                With Windsurf's AI Flow feature, you can:
                - Get AI-assisted code suggestions
                - Receive guidance on best practices
                - Debug issues with AI support
                - Add new features with natural language descriptions
                
                Would you like to open your project in Windsurf now?
                """,
                parameters={
                    "type": "object",
                    "properties": {
                        "project_path": {
                            "type": "string",
                            "description": "Path to your project"
                        }
                    },
                    "required": ["project_path"]
                }
            )
        )
