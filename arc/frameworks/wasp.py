"""
Wasp framework handler for Arc MCP Server.
"""
import os
import json
import logging
import subprocess
import shutil
import tempfile
import re
import stat
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

from arc.frameworks import register_framework, FrameworkHandler
from arc.providers import get_provider_handler

logger = logging.getLogger(__name__)

@register_framework
class WaspFrameworkHandler(FrameworkHandler):
    """
    Handler for Wasp framework deployments.
    
    Wasp is a declarative DSL for developing full-stack web applications with
    less code.
    """
    
    name = "wasp"
    display_name = "Wasp"
    description = "Wasp - The fastest way to develop full-stack web apps with React & Node.js"
    
    # Command to build a Wasp project
    BUILD_CMD = "wasp build"
    
    # Default Wasp build output directory
    DEFAULT_OUTPUT_DIR = ".wasp/build/web-app"
    
    # Default Node.js version required for Wasp
    NODE_VERSION_REQ = ">=14.0.0"
    
    # Default environment variables for Wasp
    DEFAULT_ENV_VARS = [
        "DATABASE_URL",
        "JWT_SECRET"
    ]
    
    # Common troubleshooting issues and solutions
    COMMON_ISSUES = {
        "node_version": {
            "pattern": "Node.js version must be",
            "solution": "Install the required Node.js version. Wasp requires Node.js {NODE_VERSION_REQ}."
        },
        "missing_env": {
            "pattern": "Missing required environment variable",
            "solution": "Add the required environment variables to your deployment configuration."
        },
        "build_failed": {
            "pattern": "Failed to compile",
            "solution": "Check your Wasp and client code for errors. Common issues include syntax errors in .wasp file, React component errors, or missing dependencies."
        }
    }
    
    def analyze_requirements(self, project_path: str, provider_name: str) -> Dict[str, Any]:
        """
        Analyze Wasp project requirements for deployment.
        
        Args:
            project_path: Path to the Wasp project
            provider_name: Name of the hosting provider
            
        Returns:
            Dictionary with requirements analysis
        """
        logger.info(f"Analyzing Wasp project at {project_path} for deployment to {provider_name}")
        
        # Verify that this is a Wasp project
        wasp_file = self._find_wasp_file(project_path)
        if not wasp_file:
            return {
                "success": False,
                "error": "Not a valid Wasp project. No .wasp file found."
            }
        
        # Read the .wasp file to extract information
        try:
            with open(wasp_file, 'r') as f:
                wasp_content = f.read()
        except Exception as e:
            logger.error(f"Failed to read .wasp file: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to read .wasp file: {str(e)}"
            }
        
        # Parse basic information from the .wasp file
        app_name = self._extract_app_name(wasp_content)
        uses_database = "db postgresql" in wasp_content.lower() or "db sqlite" in wasp_content.lower()
        
        # Check for package.json to identify dependencies
        dependencies = {}
        client_package_path = os.path.join(project_path, "client", "package.json")
        server_package_path = os.path.join(project_path, "server", "package.json")
        
        if os.path.exists(client_package_path):
            try:
                with open(client_package_path, 'r') as f:
                    client_pkg = json.load(f)
                dependencies["client"] = client_pkg.get("dependencies", {})
            except Exception as e:
                logger.warning(f"Failed to read client package.json: {str(e)}")
        
        if os.path.exists(server_package_path):
            try:
                with open(server_package_path, 'r') as f:
                    server_pkg = json.load(f)
                dependencies["server"] = server_pkg.get("dependencies", {})
            except Exception as e:
                logger.warning(f"Failed to read server package.json: {str(e)}")
        
        # Check if the provider supports the required features
        provider = get_provider_handler(provider_name)
        provider_capabilities = provider.get_capabilities() if hasattr(provider, "get_capabilities") else {}
        
        compatibility_issues = []
        if uses_database and not provider_capabilities.get("database_support", False):
            compatibility_issues.append(
                f"This Wasp project uses a database, but the provider {provider_name} may not support it."
            )
        
        # Get custom env vars from .env.example if it exists
        env_vars = self.DEFAULT_ENV_VARS.copy()
        env_example_path = os.path.join(project_path, ".env.example")
        if os.path.exists(env_example_path):
            try:
                with open(env_example_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            parts = line.split('=', 1)
                            if len(parts) >= 1:
                                var_name = parts[0].strip()
                                if var_name and var_name not in env_vars:
                                    env_vars.append(var_name)
            except Exception as e:
                logger.warning(f"Failed to read .env.example: {str(e)}")
        
        # Preparation steps for deployment
        preparation_steps = [
            "Ensure Node.js is installed with version {NODE_VERSION_REQ}",
            "Install Wasp CLI with 'curl -sSL https://get.wasp-lang.dev/installer.sh | sh'",
            "Run 'npm install' in both client and server directories",
            "Set up required environment variables"
        ]
        
        if compatibility_issues:
            preparation_steps.append("Address compatibility issues: " + ", ".join(compatibility_issues))
        
        return {
            "success": True,
            "framework": self.name,
            "provider": provider_name,
            "app_name": app_name or "wasp-app",
            "requirements": {
                "node_version": self.NODE_VERSION_REQ,
                "build_command": self.BUILD_CMD,
                "output_dir": self.DEFAULT_OUTPUT_DIR,
                "environment_variables": env_vars,
                "uses_database": uses_database,
                "dependencies": dependencies
            },
            "compatibility_issues": compatibility_issues,
            "preparation_steps": preparation_steps
        }
    
    def deploy(
        self, 
        project_path: str, 
        provider_name: str, 
        credentials: Dict[str, str],
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Deploy a Wasp project to a hosting provider.
        
        Args:
            project_path: Path to the Wasp project
            provider_name: Name of the hosting provider
            credentials: Provider credentials
            config: Deployment configuration
            
        Returns:
            Dictionary with deployment results
        """
        logger.info(f"Deploying Wasp project at {project_path} to {provider_name}")
        
        # Verify that this is a Wasp project
        wasp_file = self._find_wasp_file(project_path)
        if not wasp_file:
            return {
                "success": False,
                "error": "Not a valid Wasp project. No .wasp file found."
            }
        
        # Create a temporary directory for build output
        with tempfile.TemporaryDirectory() as temp_dir:
            # Build the project
            build_result = self._build_project(project_path, temp_dir, config)
            if not build_result["success"]:
                return build_result
            
            # Get the build output directory
            output_dir = build_result["output_dir"]
            
            # Get the provider handler
            provider = get_provider_handler(provider_name)
            if not provider:
                return {
                    "success": False,
                    "error": f"Unsupported provider: {provider_name}"
                }
            
            # Prepare deployment destination
            destination = config.get("destination", "")
            
            # Deploy to the provider
            deploy_result = provider.deploy(
                credentials=credentials,
                source_dir=output_dir,
                destination=destination,
                config=config
            )
            
            # Add additional information to the result
            if deploy_result["success"]:
                deploy_result["framework"] = self.name
                app_name = self._extract_app_name_from_file(wasp_file) or "wasp-app"
                deploy_result["app_name"] = app_name
            
            return deploy_result
    
    def troubleshoot(
        self, 
        project_path: str, 
        provider_name: str,
        error_log: Optional[str]
    ) -> Dict[str, Any]:
        """
        Troubleshoot Wasp deployment issues.
        
        Args:
            project_path: Path to the Wasp project
            provider_name: Name of the hosting provider
            error_log: Optional error log content
            
        Returns:
            Dictionary with troubleshooting results
        """
        logger.info(f"Troubleshooting Wasp project at {project_path} for {provider_name}")
        
        # Verify that this is a Wasp project
        wasp_file = self._find_wasp_file(project_path)
        if not wasp_file:
            return {
                "success": False,
                "error": "Not a valid Wasp project. No .wasp file found."
            }
        
        # Initialize issues and recommendations lists
        issues = []
        recommendations = []
        
        # Check for common issues in the project
        project_issues = self._check_project_issues(project_path)
        issues.extend(project_issues["issues"])
        recommendations.extend(project_issues["recommendations"])
        
        # Check the error log if provided
        if error_log:
            log_issues = self._analyze_error_log(error_log)
            issues.extend(log_issues["issues"])
            recommendations.extend(log_issues["recommendations"])
        
        # Get provider-specific troubleshooting
        provider = get_provider_handler(provider_name)
        if provider and hasattr(provider, "get_troubleshooting_info"):
            provider_info = provider.get_troubleshooting_info("wasp")
            if provider_info.get("issues"):
                issues.extend(provider_info["issues"])
            if provider_info.get("recommendations"):
                recommendations.extend(provider_info["recommendations"])
        
        # If no issues found, provide some general guidance
        if not issues:
            issues.append("No specific issues identified")
            recommendations.extend([
                "Ensure Wasp CLI is up to date with 'wasp update'",
                f"Check for Node.js compatibility (version {self.NODE_VERSION_REQ})",
                "Verify that all required environment variables are set",
                "Try running 'wasp build' locally to check for build errors"
            ])
        
        return {
            "success": True,
            "framework": self.name,
            "provider": provider_name,
            "issues": issues,
            "recommendations": recommendations
        }
    
    # Helper methods
    def _find_wasp_file(self, project_path: str) -> Optional[str]:
        """
        Find the .wasp file in the project directory.
        
        Args:
            project_path: Path to the project directory
            
        Returns:
            Path to the .wasp file if found, None otherwise
        """
        for file in os.listdir(project_path):
            if file.endswith(".wasp"):
                return os.path.join(project_path, file)
        return None
    
    def _extract_app_name(self, wasp_content: str) -> Optional[str]:
        """
        Extract the app name from Wasp file content.
        
        Args:
            wasp_content: Content of the .wasp file
            
        Returns:
            App name if found, None otherwise
        """
        # Look for app declaration
        app_match = re.search(r'app\s+(\w+)\s*{', wasp_content)
        if app_match:
            return app_match.group(1)
        
        # Look for title declaration
        title_match = re.search(r'title\s*:\s*"([^"]+)"', wasp_content)
        if title_match:
            return title_match.group(1)
        
        return None
    
    def _extract_app_name_from_file(self, wasp_file: str) -> Optional[str]:
        """
        Extract the app name from a Wasp file.
        
        Args:
            wasp_file: Path to the .wasp file
            
        Returns:
            App name if found, None otherwise
        """
        try:
            with open(wasp_file, 'r') as f:
                wasp_content = f.read()
            return self._extract_app_name(wasp_content)
        except Exception as e:
            logger.error(f"Failed to read .wasp file: {str(e)}")
            return None
    
    def _build_project(self, project_path: str, temp_dir: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build the Wasp project.
        
        Args:
            project_path: Path to the Wasp project
            temp_dir: Temporary directory for build output
            config: Build configuration
            
        Returns:
            Dictionary with build results
        """
        logger.info(f"Building Wasp project at {project_path}")
        
        # Determine the build command
        build_cmd = config.get("build_command", self.BUILD_CMD)
        
        # Set up environment variables for the build
        env = os.environ.copy()
        env_vars = config.get("env", {})
        for key, value in env_vars.items():
            env[key] = value
        
        # Set up the output directory
        output_dir_name = config.get("output_dir", self.DEFAULT_OUTPUT_DIR)
        output_dir = os.path.join(project_path, output_dir_name)
        
        try:
            # Run the build command
            process = subprocess.Popen(
                build_cmd,
                shell=True,
                cwd=project_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                text=True
            )
            stdout, stderr = process.communicate()
            
            if process.returncode != 0:
                logger.error(f"Build failed: {stderr}")
                return {
                    "success": False,
                    "error": f"Build failed with exit code {process.returncode}",
                    "details": stderr
                }
            
            # Copy the build output to the temporary directory
            if os.path.exists(output_dir):
                dest_dir = os.path.join(temp_dir, "build")
                shutil.copytree(output_dir, dest_dir)
                logger.info(f"Build output copied to {dest_dir}")
                return {
                    "success": True,
                    "output_dir": dest_dir,
                    "message": "Build completed successfully"
                }
            else:
                logger.error(f"Build output directory not found: {output_dir}")
                return {
                    "success": False,
                    "error": f"Build output directory not found: {output_dir}"
                }
                
        except Exception as e:
            logger.error(f"Build process error: {str(e)}")
            return {
                "success": False,
                "error": f"Build process error: {str(e)}"
            }
    
    def _check_project_issues(self, project_path: str) -> Dict[str, List[str]]:
        """
        Check for common issues in the Wasp project.
        
        Args:
            project_path: Path to the Wasp project
            
        Returns:
            Dictionary with issues and recommendations
        """
        issues = []
        recommendations = []
        
        # Check if .wasp/build exists but is empty
        build_dir = os.path.join(project_path, ".wasp/build")
        if os.path.exists(build_dir) and not os.listdir(build_dir):
            issues.append("Build directory exists but is empty")
            recommendations.append("Run 'wasp build' to generate the build output")
        
        # Check for node_modules
        client_node_modules = os.path.join(project_path, "client/node_modules")
        server_node_modules = os.path.join(project_path, "server/node_modules")
        
        if not os.path.exists(client_node_modules):
            issues.append("Client dependencies not installed")
            recommendations.append("Run 'npm install' in the client directory")
        
        if not os.path.exists(server_node_modules):
            issues.append("Server dependencies not installed")
            recommendations.append("Run 'npm install' in the server directory")
        
        # Check for .env file
        env_file = os.path.join(project_path, ".env")
        env_example_file = os.path.join(project_path, ".env.example")
        
        if not os.path.exists(env_file) and os.path.exists(env_example_file):
            issues.append("Missing .env file")
            recommendations.append("Create a .env file based on .env.example")
        
        # Check for common React errors in client code
        client_src_dir = os.path.join(project_path, "client/src")
        if os.path.exists(client_src_dir):
            for root, _, files in os.walk(client_src_dir):
                for file in files:
                    if file.endswith((".jsx", ".tsx", ".js", ".ts")):
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, 'r') as f:
                                content = f.read()
                                # Check for missing imports
                                if "import React" not in content and ("useState" in content or "useEffect" in content):
                                    issues.append(f"Possible missing React import in {os.path.relpath(file_path, project_path)}")
                                    recommendations.append(f"Add 'import React from \"react\"' to {os.path.relpath(file_path, project_path)}")
                        except Exception:
                            pass
        
        return {
            "issues": issues,
            "recommendations": recommendations
        }
    
    def _analyze_error_log(self, error_log: str) -> Dict[str, List[str]]:
        """
        Analyze the error log for common issues.
        
        Args:
            error_log: Content of the error log
            
        Returns:
            Dictionary with issues and recommendations
        """
        issues = []
        recommendations = []
        
        # Check for common issues based on error patterns
        for issue_key, issue_info in self.COMMON_ISSUES.items():
            pattern = issue_info["pattern"]
            if pattern in error_log:
                solution = issue_info["solution"]
                solution = solution.replace("{NODE_VERSION_REQ}", self.NODE_VERSION_REQ)
                
                issues.append(f"Detected {issue_key} issue")
                recommendations.append(solution)
        
        # Check for specific error messages
        if "Module not found: Error: Can't resolve" in error_log:
            # Extract the missing module name
            match = re.search(r"Can't resolve '([^']+)'", error_log)
            if match:
                module_name = match.group(1)
                issues.append(f"Missing dependency: {module_name}")
                recommendations.append(f"Install the missing dependency with 'npm install {module_name}'")
        
        if "Failed to connect to database" in error_log:
            issues.append("Database connection issue")
            recommendations.append("Verify that the DATABASE_URL environment variable is correctly set")
            recommendations.append("Check if the database server is running and accessible")
        
        if "CORS" in error_log:
            issues.append("CORS (Cross-Origin Resource Sharing) issue")
            recommendations.append("Configure CORS settings in your Wasp app")
            recommendations.append("Ensure that the client-side origin is allowed in your CORS configuration")
        
        return {
            "issues": issues,
            "recommendations": recommendations
        }
"""
