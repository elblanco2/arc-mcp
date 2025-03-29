"""Netlify provider handler for Arc MCP."""

import asyncio
import json
import logging
import os
import re
import subprocess
from typing import Dict, List, Optional

from arc_mcp.providers.base import ProviderHandler

logger = logging.getLogger("arc-mcp.providers.netlify")

class NetlifyProviderHandler(ProviderHandler):
    """Handler for Netlify hosting provider."""
    
    async def validate_credentials(self, credentials: Dict[str, str]) -> bool:
        """Validate Netlify credentials.
        
        Args:
            credentials: Netlify credentials
            
        Returns:
            True if credentials are valid, False otherwise
        """
        api_key = credentials.get("api_key")
        if not api_key:
            logger.error("Missing API key in Netlify credentials")
            return False
        
        # Use Netlify CLI to validate
        try:
            # Create temporary auth.json file
            temp_auth_path = os.path.expanduser("~/.netlify/temp_auth.json")
            os.makedirs(os.path.dirname(temp_auth_path), exist_ok=True)
            
            with open(temp_auth_path, "w") as f:
                json.dump({"auth": {"token": api_key}}, f)
            
            # Run netlify status command
            process = await asyncio.create_subprocess_exec(
                "netlify", "status",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env={**os.environ, "NETLIFY_AUTH_PATH": temp_auth_path}
            )
            
            stdout, stderr = await process.communicate()
            
            # Clean up
            os.remove(temp_auth_path)
            
            # Check result
            if process.returncode == 0:
                logger.info("Netlify credentials validated successfully")
                return True
            else:
                logger.error(f"Netlify credential validation failed: {stderr.decode()}")
                return False
                
        except Exception as e:
            logger.error(f"Error validating Netlify credentials: {str(e)}")
            return False
    
    async def deploy(self, path: str, credentials: Dict[str, str], options: Dict) -> Dict:
        """Deploy a project to Netlify.
        
        Args:
            path: Path to the prepared project
            credentials: Netlify credentials
            options: Deployment options
            
        Returns:
            Deployment result with URL and other details
        """
        api_key = credentials.get("api_key")
        if not api_key:
            raise ValueError("Missing API key in Netlify credentials")
        
        site_name = options.get("site_name", "")
        team_name = options.get("team_name", "")
        
        # Create deploy command
        deploy_cmd = ["netlify", "deploy", "--dir", path, "--prod"]
        
        if site_name:
            deploy_cmd.extend(["--site", site_name])
        
        if team_name:
            deploy_cmd.extend(["--team", team_name])
        
        # Create temporary auth.json file
        temp_auth_path = os.path.expanduser("~/.netlify/temp_auth.json")
        os.makedirs(os.path.dirname(temp_auth_path), exist_ok=True)
        
        with open(temp_auth_path, "w") as f:
            json.dump({"auth": {"token": api_key}}, f)
        
        try:
            # Run deploy command
            process = await asyncio.create_subprocess_exec(
                *deploy_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env={**os.environ, "NETLIFY_AUTH_PATH": temp_auth_path}
            )
            
            stdout, stderr = await process.communicate()
            stdout_text = stdout.decode()
            stderr_text = stderr.decode()
            
            # Clean up
            os.remove(temp_auth_path)
            
            if process.returncode != 0:
                logger.error(f"Netlify deployment failed: {stderr_text}")
                raise RuntimeError(f"Netlify deployment failed: {stderr_text}")
            
            # Extract site URL from output
            url_match = re.search(r"Website URL:\s+(\S+)", stdout_text)
            site_url = url_match.group(1) if url_match else ""
            
            # Extract site ID from output
            site_id_match = re.search(r"Site ID:\s+(\S+)", stdout_text)
            site_id = site_id_match.group(1) if site_id_match else ""
            
            logger.info(f"Netlify deployment successful. URL: {site_url}")
            
            return {
                "url": site_url,
                "site_id": site_id,
                "logs": stdout_text
            }
            
        except Exception as e:
            logger.error(f"Error deploying to Netlify: {str(e)}")
            raise
    
    async def analyze_logs(self, logs: str) -> List[Dict]:
        """Analyze Netlify deployment logs to identify issues.
        
        Args:
            logs: Deployment logs
            
        Returns:
            List of identified issues
        """
        issues = []
        
        # Common Netlify deployment issues
        if "Error: Not authorized" in logs:
            issues.append({
                "id": "netlify_auth_error",
                "type": "auth_error",
                "message": "Authentication failed. Please check your Netlify API key.",
                "severity": "high"
            })
        
        if "Error: No such site" in logs:
            issues.append({
                "id": "netlify_site_not_found",
                "type": "site_error",
                "message": "Site not found. Please check the site name or create a new site.",
                "severity": "high"
            })
        
        if "Build failed" in logs:
            # Extract build error message
            build_error_match = re.search(r"Build failed: (.*)", logs)
            build_error = build_error_match.group(1) if build_error_match else "Unknown build error"
            
            issues.append({
                "id": "netlify_build_error",
                "type": "build_error",
                "message": f"Build failed: {build_error}",
                "severity": "high"
            })
        
        if "Error: Build script returned non-zero exit code" in logs:
            issues.append({
                "id": "netlify_build_script_error",
                "type": "build_error",
                "message": "Build script failed. Check your build command in netlify.toml.",
                "severity": "high"
            })
        
        if "Deploy failed" in logs:
            issues.append({
                "id": "netlify_deploy_error",
                "type": "deployment_error",
                "message": "Deployment failed. Check your Netlify site settings.",
                "severity": "high"
            })
        
        # If no specific issues found but deployment failed
        if not issues and ("error" in logs.lower() or "failed" in logs.lower()):
            issues.append({
                "id": "netlify_unknown_error",
                "type": "unknown_error",
                "message": "Unknown error occurred during deployment. Check the logs for details.",
                "severity": "medium"
            })
        
        return issues