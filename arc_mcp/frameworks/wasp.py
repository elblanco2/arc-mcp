"""Wasp framework handler for Arc MCP."""

import asyncio
import logging
import os
import shutil
import subprocess
from typing import Dict, List, Optional

from arc_mcp.frameworks.base import FrameworkHandler

logger = logging.getLogger("arc-mcp.frameworks.wasp")

class WaspFrameworkHandler(FrameworkHandler):
    """Handler for Wasp framework projects."""
    
    async def prepare_for_deployment(self, path: str, provider: str, options: Dict) -> str:
        """Prepare a Wasp project for deployment.
        
        Args:
            path: Path to the Wasp project
            provider: Target hosting provider
            options: Deployment options
            
        Returns:
            Path to the prepared project
        """
        logger.info(f"Preparing Wasp project at {path} for deployment to {provider}")
        
        # Validate the project
        validation = self.validate_project(path)
        if not validation["valid"]:
            issues_str = ", ".join([issue["message"] for issue in validation["issues"]])
            raise ValueError(f"Invalid Wasp project: {issues_str}")
        
        # Build the project
        build_path = os.path.join(path, ".build")
        os.makedirs(build_path, exist_ok=True)
        
        try:
            # Run wasp build
            logger.info("Building Wasp project...")
            build_cmd = ["wasp", "build"]
            
            process = await asyncio.create_subprocess_exec(
                *build_cmd,
                cwd=path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                logger.error(f"Build failed: {stderr.decode()}")
                raise RuntimeError(f"Failed to build Wasp project: {stderr.decode()}")
            
            logger.info("Build completed successfully")
            
            # Modify configuration for provider if needed
            if provider == "netlify":
                self._prepare_for_netlify(path, build_path, options)
            elif provider == "vercel":
                self._prepare_for_vercel(path, build_path, options)
            
            return build_path
        except Exception as e:
            logger.error(f"Error preparing Wasp project: {str(e)}")
            raise
    
    def _prepare_for_netlify(self, project_path: str, build_path: str, options: Dict):
        """Prepare a Wasp project for Netlify deployment."""
        # Create netlify.toml configuration
        netlify_config = f"""
[build]
  publish = ".wasp/build/web/app"
  command = "cd .wasp && npm install && npm run build"

[functions]
  directory = ".wasp/build/server/src/server"

[[redirects]]
  from = "/api/*"
  to = "/.netlify/functions/server/:splat"
  status = 200
"""
        with open(os.path.join(project_path, "netlify.toml"), "w") as f:
            f.write(netlify_config)
        
        logger.info("Created netlify.toml configuration")
    
    def _prepare_for_vercel(self, project_path: str, build_path: str, options: Dict):
        """Prepare a Wasp project for Vercel deployment."""
        # Create vercel.json configuration
        vercel_config = {
            "version": 2,
            "builds": [
                {
                    "src": ".wasp/build/web/app",
                    "use": "@vercel/static"
                },
                {
                    "src": ".wasp/build/server/src/server/index.js",
                    "use": "@vercel/node"
                }
            ],
            "routes": [
                {
                    "src": "/api/(.*)",
                    "dest": "/.wasp/build/server/src/server/index.js"
                },
                {
                    "src": "/(.*)",
                    "dest": "/.wasp/build/web/app/$1"
                }
            ]
        }
        
        import json
        with open(os.path.join(project_path, "vercel.json"), "w") as f:
            json.dump(vercel_config, f, indent=2)
        
        logger.info("Created vercel.json configuration")
    
    async def get_solutions(self, issues: List[Dict], provider: str) -> List[Dict]:
        """Get Wasp-specific solutions for deployment issues.
        
        Args:
            issues: List of detected issues
            provider: The hosting provider
            
        Returns:
            List of solution recommendations
        """
        solutions = []
        
        for issue in issues:
            issue_type = issue.get("type")
            
            if issue_type == "build_error":
                solutions.append({
                    "issue_id": issue.get("id"),
                    "steps": [
                        "Check that you have the latest version of Wasp installed",
                        "Ensure all dependencies are listed in your package.json",
                        "Try running 'wasp build' locally to see detailed error messages",
                        "Check for syntax errors in your main.wasp file"
                    ]
                })
            elif issue_type == "deployment_error":
                if provider == "netlify":
                    solutions.append({
                        "issue_id": issue.get("id"),
                        "steps": [
                            "Verify your Netlify account has the necessary permissions",
                            "Check that your site name is available on Netlify",
                            "Ensure your Netlify token is valid",
                            "Check for any build command customizations in netlify.toml"
                        ]
                    })
                elif provider == "vercel":
                    solutions.append({
                        "issue_id": issue.get("id"),
                        "steps": [
                            "Verify your Vercel account has the necessary permissions",
                            "Check that your project name is available on Vercel",
                            "Ensure your Vercel token is valid",
                            "Check for any configuration issues in vercel.json"
                        ]
                    })
            elif issue_type == "database_error":
                solutions.append({
                    "issue_id": issue.get("id"),
                    "steps": [
                        "Verify your database connection string is correct",
                        "Check if your database server is accessible from your hosting provider",
                        "Ensure your database schema matches your Wasp entities",
                        "Try running prisma migrations locally first"
                    ]
                })
        
        return solutions
    
    def validate_project(self, path: str) -> Dict:
        """Validate a Wasp project.
        
        Args:
            path: Path to the project
            
        Returns:
            Validation result with status and issues
        """
        issues = []
        
        # Check if main.wasp exists
        main_wasp_path = os.path.join(path, "main.wasp")
        if not os.path.exists(main_wasp_path):
            issues.append({
                "type": "missing_file",
                "message": "main.wasp file is missing",
                "path": main_wasp_path
            })
        
        # Check if package.json exists
        package_json_path = os.path.join(path, "package.json")
        if not os.path.exists(package_json_path):
            issues.append({
                "type": "missing_file",
                "message": "package.json file is missing",
                "path": package_json_path
            })
        
        # Check for node_modules directory
        node_modules_path = os.path.join(path, "node_modules")
        if not os.path.exists(node_modules_path):
            issues.append({
                "type": "missing_directory",
                "message": "node_modules directory is missing, run 'npm install' first",
                "path": node_modules_path
            })
        
        # Validate main.wasp syntax (basic check)
        if os.path.exists(main_wasp_path):
            try:
                with open(main_wasp_path, "r") as f:
                    content = f.read()
                
                # Basic check for app declaration
                if "app " not in content:
                    issues.append({
                        "type": "syntax_error",
                        "message": "Missing app declaration in main.wasp",
                        "path": main_wasp_path
                    })
            except Exception as e:
                issues.append({
                    "type": "read_error",
                    "message": f"Error reading main.wasp: {str(e)}",
                    "path": main_wasp_path
                })
        
        return {
            "valid": len(issues) == 0,
            "issues": issues
        }