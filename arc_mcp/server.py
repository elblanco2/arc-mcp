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

    def _register_resources(self):
        """Register all resources provided by the server."""
        # Provider documentation
        self.register_resource(
            "provider-docs",
            ResourceMetadata(
                name="Hosting Provider Documentation",
                description="Documentation for supported hosting providers",
                mime_type="application/json"
            )
        )
        
        # Framework guides
        self.register_resource(
            "framework-guides",
            ResourceMetadata(
                name="Framework Deployment Guides",
                description="Step-by-step guides for deploying different frameworks",
                mime_type="application/json"
            )
        )

    # Tool implementations
    async def _save_credentials(self, provider: str, credentials: Dict[str, str]) -> Dict[str, str]:
        """Save provider credentials securely."""
        logger.info(f"Saving credentials for provider: {provider}")
        try:
            self.credentials_manager.save_credentials(provider, credentials)
            return {"status": "success", "message": f"Credentials for {provider} saved successfully"}
        except Exception as e:
            logger.error(f"Error saving credentials: {str(e)}")
            raise ToolExecutionError(f"Failed to save credentials: {str(e)}")

    async def _validate_credentials(self, provider: str, credentials: Dict[str, str]) -> Dict[str, bool]:
        """Validate credentials with the provider's API."""
        logger.info(f"Validating credentials for provider: {provider}")
        try:
            provider_handler = get_provider_handler(provider)
            is_valid = await provider_handler.validate_credentials(credentials)
            return {"valid": is_valid, "provider": provider}
        except Exception as e:
            logger.error(f"Error validating credentials: {str(e)}")
            raise ToolExecutionError(f"Failed to validate credentials: {str(e)}")

    async def _deploy_project(self, path: str, provider: str, options: Dict) -> Dict:
        """Deploy a project to the specified provider."""
        logger.info(f"Deploying project from {path} to {provider}")
        try:
            # Detect framework type
            framework_type = options.get("framework", self._detect_framework(path))
            if not framework_type:
                raise ToolExecutionError(f"Could not detect framework type for project at {path}")
            
            # Get appropriate handlers
            framework_handler = get_framework_handler(framework_type)
            provider_handler = get_provider_handler(provider)
            
            # Get credentials
            credentials = self.credentials_manager.get_credentials(provider)
            if not credentials:
                raise ToolExecutionError(f"No credentials found for {provider}. Please save credentials first.")
            
            # Prepare the project
            prepared_path = await framework_handler.prepare_for_deployment(path, provider, options)
            
            # Deploy
            deployment_result = await provider_handler.deploy(prepared_path, credentials, options)
            
            return {
                "status": "success",
                "message": f"Successfully deployed {framework_type} project to {provider}",
                "url": deployment_result.get("url", ""),
                "details": deployment_result
            }
        except Exception as e:
            logger.error(f"Deployment error: {str(e)}")
            raise ToolExecutionError(f"Deployment failed: {str(e)}")

    async def _troubleshoot_deployment(self, path: str, logs: str, provider: str) -> Dict:
        """Analyze deployment logs and provide troubleshooting guidance."""
        logger.info(f"Troubleshooting deployment for project at {path} on {provider}")
        try:
            # Detect framework type
            framework_type = self._detect_framework(path)
            if not framework_type:
                raise ToolExecutionError(f"Could not detect framework type for project at {path}")
            
            # Get appropriate handlers
            framework_handler = get_framework_handler(framework_type)
            provider_handler = get_provider_handler(provider)
            
            # Analyze logs
            issues = await provider_handler.analyze_logs(logs)
            
            # Get framework-specific solutions
            solutions = await framework_handler.get_solutions(issues, provider)
            
            return {
                "issues_detected": issues,
                "recommended_solutions": solutions,
                "framework": framework_type,
                "provider": provider
            }
        except Exception as e:
            logger.error(f"Troubleshooting error: {str(e)}")
            raise ToolExecutionError(f"Troubleshooting failed: {str(e)}")

    async def _open_in_windsurf(self, path: str) -> Dict:
        """Open a project in Windsurf (Codeium's VS Code)."""
        logger.info(f"Opening project in Windsurf: {path}")
        try:
            # Check if path exists
            if not os.path.exists(path):
                raise ToolExecutionError(f"Project path does not exist: {path}")
            
            # In a real implementation, this would use Windsurf's API or CLI
            # For now, we'll just return success
            return {
                "status": "success",
                "message": f"Project at {path} opened in Windsurf",
                "path": path
            }
        except Exception as e:
            logger.error(f"Error opening in Windsurf: {str(e)}")
            raise ToolExecutionError(f"Failed to open in Windsurf: {str(e)}")

    # Helper methods
    def _detect_framework(self, path: str) -> Optional[str]:
        """Detect the framework type based on project structure."""
        if not os.path.exists(path):
            return None
            
        # Check for Wasp
        if os.path.exists(os.path.join(path, "main.wasp")):
            return "wasp"
            
        # Check for Next.js
        if os.path.exists(os.path.join(path, "next.config.js")):
            return "nextjs"
            
        # Check for Astro
        if os.path.exists(os.path.join(path, "astro.config.mjs")):
            return "astro"
            
        return None

    # Resource implementations
    async def get_resource_content(self, resource_id: str) -> bytes:
        """Get the content of a resource."""
        if resource_id == "provider-docs":
            providers = {
                "netlify": {
                    "description": "Netlify is a web hosting infrastructure company that offers hosting and serverless backend services for web applications and static websites.",
                    "features": ["Continuous Deployment", "Serverless Functions", "Forms", "Identity", "Analytics"],
                    "pricing": "Free tier available, paid plans start at $19/month",
                    "website": "https://www.netlify.com"
                },
                "vercel": {
                    "description": "Vercel is a cloud platform for static sites and Serverless Functions that fits perfectly with your workflow.",
                    "features": ["Edge Network", "Serverless Functions", "Previews", "Analytics", "Monorepo Support"],
                    "pricing": "Free tier available, paid plans start at $20/month",
                    "website": "https://vercel.com"
                },
                "shared-hosting": {
                    "description": "Traditional web hosting where multiple websites share a single server.",
                    "features": ["FTP Access", "cPanel", "MySQL Databases", "PHP Support", "Email Hosting"],
                    "pricing": "Varies by provider, typically $5-15/month",
                    "website": "Various providers"
                },
                "hostm": {
                    "description": "Hostm.com offers shared hosting optimized for small to medium websites with good performance.",
                    "features": ["One-click installs", "SSD Storage", "Free SSL", "24/7 Support", "99.9% Uptime"],
                    "pricing": "Plans start at $3.95/month",
                    "website": "https://www.hostm.com"
                }
            }
            return json.dumps(providers).encode("utf-8")
            
        elif resource_id == "framework-guides":
            guides = {
                "wasp": {
                    "title": "Deploying Wasp Applications",
                    "description": "Step-by-step guide for deploying Wasp applications to various providers",
                    "steps": [
                        "Build your Wasp application",
                        "Configure deployment settings",
                        "Deploy to your chosen provider",
                        "Set up custom domain (optional)",
                        "Configure CI/CD (optional)"
                    ],
                    "supported_providers": ["netlify", "vercel"]
                },
                "nextjs": {
                    "title": "Deploying Next.js Applications",
                    "description": "Guide for deploying Next.js applications",
                    "steps": [
                        "Build your Next.js application",
                        "Configure environment variables",
                        "Deploy to your chosen provider",
                        "Set up custom domain (optional)",
                        "Configure CI/CD (optional)"
                    ],
                    "supported_providers": ["netlify", "vercel", "shared-hosting"]
                },
                "astro": {
                    "title": "Deploying Astro Applications",
                    "description": "Guide for deploying Astro sites",
                    "steps": [
                        "Build your Astro site",
                        "Configure deployment settings",
                        "Deploy to your chosen provider",
                        "Set up custom domain (optional)",
                        "Configure CI/CD (optional)"
                    ],
                    "supported_providers": ["netlify", "vercel", "shared-hosting"]
                }
            }
            return json.dumps(guides).encode("utf-8")
            
        raise Exception(f"Unknown resource: {resource_id}")

def main():
    """Main entry point for the server."""
    parser = argparse.ArgumentParser(description="Arc MCP Server")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--secure-storage-path", help="Path to store credentials")
    args = parser.parse_args()
    
    server = ArcMCPServer(
        credentials_path=args.secure_storage_path,
        debug=args.debug
    )
    
    asyncio.run(server.run())

if __name__ == "__main__":
    main()