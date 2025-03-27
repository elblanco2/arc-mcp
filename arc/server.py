"""
Main MCP server implementation for Arc.
"""
import os
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
import json

# Assuming use of FastMCP for implementation
from fastmcp import MCPServer, Tool, Resource, Prompt

from arc.credentials import CredentialManager
from arc.frameworks import get_framework_handler
from arc.providers import get_provider_handler

logger = logging.getLogger(__name__)

class ArcServer(MCPServer):
    """
    Arc MCP Server for simplified web application deployment.
    Implements the Model Context Protocol to expose tools for deploying
    web applications to various hosting environments.
    """
    
    def __init__(self, debug: bool = False):
        super().__init__(
            name="arc",
            description="Arc MCP Server - Simplified web application deployment",
            version="0.1.0"
        )
        
        self.debug = debug
        self.credential_manager = CredentialManager()
        
        # Register all tools
        self._register_tools()
        # Register all resources
        self._register_resources()
        # Register all prompts
        self._register_prompts()
        
        logger.info("Arc MCP Server initialized")
    
    def _register_tools(self):
        """Register all tools with the MCP server."""
        
        @self.tool("authenticate_provider")
        def authenticate_provider(provider_name: str, credentials: Dict[str, str]) -> Dict[str, Any]:
            """
            Store authentication credentials for a hosting provider.
            
            Args:
                provider_name: Name of the hosting provider (e.g., 'netlify', 'vercel', 'shared_hosting', 'hostm')
                credentials: Dictionary of credentials required by the provider
                
            Returns:
                Dictionary with authentication status and provider information
            """
            logger.info(f"Authenticating with provider: {provider_name}")
            
            provider = get_provider_handler(provider_name)
            if not provider:
                return {"success": False, "error": f"Unsupported provider: {provider_name}"}
            
            # Validate credentials
            validation_result = provider.validate_credentials(credentials)
            if not validation_result["success"]:
                return validation_result
            
            # Store credentials securely
            self.credential_manager.store_credentials(provider_name, credentials)
            
            return {
                "success": True,
                "provider": provider_name,
                "message": f"Successfully authenticated with {provider_name}"
            }
        
        @self.tool("check_server_status")
        def check_server_status(provider_name: str, site_id: Optional[str] = None) -> Dict[str, Any]:
            """
            Check the status of the configured server.
            
            Args:
                provider_name: Name of the hosting provider
                site_id: Optional identifier for the specific site
                
            Returns:
                Dictionary with server status information
            """
            logger.info(f"Checking server status for provider: {provider_name}")
            
            provider = get_provider_handler(provider_name)
            if not provider:
                return {"success": False, "error": f"Unsupported provider: {provider_name}"}
            
            # Get stored credentials
            credentials = self.credential_manager.get_credentials(provider_name)
            if not credentials:
                return {"success": False, "error": f"No credentials found for {provider_name}"}
            
            # Check status
            return provider.check_status(credentials, site_id)
        
        @self.tool("analyze_requirements")
        def analyze_requirements(
            framework_name: str, 
            provider_name: str,
            project_path: str
        ) -> Dict[str, Any]:
            """
            Analyze deployment requirements for a framework/provider combination.
            
            Args:
                framework_name: Name of the framework (e.g., 'wasp', 'nextjs')
                provider_name: Name of the hosting provider
                project_path: Path to the project directory
                
            Returns:
                Dictionary with requirements analysis
            """
            logger.info(f"Analyzing requirements for {framework_name} on {provider_name}")
            
            framework = get_framework_handler(framework_name)
            if not framework:
                return {"success": False, "error": f"Unsupported framework: {framework_name}"}
            
            provider = get_provider_handler(provider_name)
            if not provider:
                return {"success": False, "error": f"Unsupported provider: {provider_name}"}
            
            # Check if project path exists
            if not os.path.isdir(project_path):
                return {"success": False, "error": f"Project path does not exist: {project_path}"}
            
            # Analyze requirements
            return framework.analyze_requirements(project_path, provider_name)
        
        @self.tool("deploy_framework")
        def deploy_framework(
            framework_name: str,
            provider_name: str,
            project_path: str,
            config: Optional[Dict[str, Any]] = None
        ) -> Dict[str, Any]:
            """
            Deploy a framework to the specified hosting provider.
            
            Args:
                framework_name: Name of the framework
                provider_name: Name of the hosting provider
                project_path: Path to the project directory
                config: Optional configuration parameters
                
            Returns:
                Dictionary with deployment results
            """
            logger.info(f"Deploying {framework_name} to {provider_name}")
            
            framework = get_framework_handler(framework_name)
            if not framework:
                return {"success": False, "error": f"Unsupported framework: {framework_name}"}
            
            provider = get_provider_handler(provider_name)
            if not provider:
                return {"success": False, "error": f"Unsupported provider: {provider_name}"}
            
            # Get stored credentials
            credentials = self.credential_manager.get_credentials(provider_name)
            if not credentials:
                return {"success": False, "error": f"No credentials found for {provider_name}"}
            
            # Check if project path exists
            if not os.path.isdir(project_path):
                return {"success": False, "error": f"Project path does not exist: {project_path}"}
            
            # Prepare default config if not provided
            if config is None:
                config = {}
            
            # Deploy
            return framework.deploy(project_path, provider_name, credentials, config)
        
        @self.tool("troubleshoot_deployment")
        def troubleshoot_deployment(
            framework_name: str,
            provider_name: str,
            project_path: str,
            error_log: Optional[str] = None
        ) -> Dict[str, Any]:
            """
            Analyze deployment errors and suggest solutions.
            
            Args:
                framework_name: Name of the framework
                provider_name: Name of the hosting provider
                project_path: Path to the project directory
                error_log: Optional error log content
                
            Returns:
                Dictionary with troubleshooting results
            """
            logger.info(f"Troubleshooting deployment for {framework_name} on {provider_name}")
            
            framework = get_framework_handler(framework_name)
            if not framework:
                return {"success": False, "error": f"Unsupported framework: {framework_name}"}
            
            provider = get_provider_handler(provider_name)
            if not provider:
                return {"success": False, "error": f"Unsupported provider: {provider_name}"}
            
            # Check if project path exists
            if not os.path.isdir(project_path):
                return {"success": False, "error": f"Project path does not exist: {project_path}"}
            
            # Troubleshoot
            return framework.troubleshoot(project_path, provider_name, error_log)
    
    def _register_resources(self):
        """Register all resources with the MCP server."""
        
        @self.resource("supported_frameworks")
        def supported_frameworks() -> List[Dict[str, Any]]:
            """
            Get a list of supported frameworks.
            
            Returns:
                List of dictionaries with framework information
            """
            from arc.frameworks import list_frameworks
            return list_frameworks()
        
        @self.resource("supported_providers")
        def supported_providers() -> List[Dict[str, Any]]:
            """
            Get a list of supported hosting providers.
            
            Returns:
                List of dictionaries with provider information
            """
            from arc.providers import list_providers
            return list_providers()
        
        @self.resource("deployment_status")
        def deployment_status(provider_name: str, site_id: Optional[str] = None) -> Dict[str, Any]:
            """
            Get the current deployment status.
            
            Args:
                provider_name: Name of the hosting provider
                site_id: Optional identifier for the specific site
                
            Returns:
                Dictionary with deployment status
            """
            provider = get_provider_handler(provider_name)
            if not provider:
                return {"success": False, "error": f"Unsupported provider: {provider_name}"}
            
            # Get stored credentials
            credentials = self.credential_manager.get_credentials(provider_name)
            if not credentials:
                return {"success": False, "error": f"No credentials found for {provider_name}"}
            
            # Get deployment status
            return provider.get_deployment_status(credentials, site_id)
    
    def _register_prompts(self):
        """Register all prompts with the MCP server."""
        
        self.prompt(
            id="introduction",
            content="""
            I'm Arc, your deployment assistant. I can help you deploy web applications to various hosting providers, with special expertise in shared hosting environments.
            
            Here's what I can do for you:
            - Help authenticate with hosting providers
            - Analyze your project for deployment requirements
            - Deploy your web application to your chosen hosting environment
            - Troubleshoot deployment issues
            - Guide you through the entire deployment process
            
            I currently support the following frameworks:
            {supported_frameworks}
            
            And the following hosting providers:
            {supported_providers}
            
            To get started, you can ask me to deploy your application or help you set up authentication with a hosting provider.
            """,
            variables=["supported_frameworks", "supported_providers"]
        )
        
        self.prompt(
            id="deployment_guide",
            content="""
            Here's a step-by-step guide to deploying your {framework_name} application to {provider_name}:
            
            1. First, authenticate with {provider_name}
               - Use the authenticate_provider tool with your credentials
            
            2. Analyze your project requirements
               - Use the analyze_requirements tool to check for any missing configurations
            
            3. Prepare your project based on the analysis results
               - Address any issues identified in the analysis
            
            4. Deploy your application
               - Use the deploy_framework tool to start the deployment
            
            5. Monitor deployment status
               - Check the deployment_status resource for updates
            
            6. Troubleshoot if needed
               - If you encounter any issues, use the troubleshoot_deployment tool
            
            Would you like me to guide you through this process?
            """,
            variables=["framework_name", "provider_name"]
        )
    
    def start(self, host: str = "localhost", port: int = 8000):
        """Start the MCP server."""
        logger.info(f"Starting Arc MCP Server on {host}:{port}")
        # Assuming FastMCP has a run method
        self.run(host=host, port=port)
