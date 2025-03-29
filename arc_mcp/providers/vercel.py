"""Vercel provider handler for Arc MCP."""

import asyncio
import json
import logging
import os
import re
import subprocess
from typing import Dict, List, Optional

from arc_mcp.providers.base import ProviderHandler

logger = logging.getLogger("arc-mcp.providers.vercel")

class VercelProviderHandler(ProviderHandler):
    """Handler for Vercel hosting provider."""
    
    async def validate_credentials(self, credentials: Dict[str, str]) -> bool:
        """Validate Vercel credentials.
        
        Args:
            credentials: Vercel credentials
            
        Returns:
            True if credentials are valid, False otherwise
        """
        token = credentials.get("token")
        if not token:
            logger.error("Missing token in Vercel credentials")
            return False
        
        try:
            # Create .vercel/credentials.json file
            creds_dir = os.path.expanduser("~/.vercel")
            creds_path = os.path.join(creds_dir, "credentials.json")
            os.makedirs(creds_dir, exist_ok=True)
            
            with open(creds_path, "w") as f:
                json.dump({"token": token}, f)
            
            # Run vercel whoami
            process = await asyncio.create_subprocess_exec(
                "vercel", "whoami",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                logger.info("Vercel credentials validated successfully")
                return True
            else:
                logger.error(f"Vercel credential validation failed: {stderr.decode()}")
                return False
                
        except Exception as e:
            logger.error(f"Error validating Vercel credentials: {str(e)}")
            return False
        finally:
            # Clean up (in production, you might want to handle this differently)
            if os.path.exists(creds_path):
                os.remove(creds_path)
    
    async def deploy(self, path: str, credentials: Dict[str, str], options: Dict) -> Dict:
        """Deploy a project to Vercel.
        
        Args:
            path: Path to the prepared project
            credentials: Vercel credentials
            options: Deployment options
            
        Returns:
            Deployment result with URL and other details
        """
        token = credentials.get("token")
        if not token:
            raise ValueError("Missing token in Vercel credentials")
        
        project_name = options.get("project_name", "")
        org_id = options.get("org_id", "")
        
        # Setup credentials
        creds_dir = os.path.expanduser("~/.vercel")
        creds_path = os.path.join(creds_dir, "credentials.json")
        os.makedirs(creds_dir, exist_ok=True)
        
        with open(creds_path, "w") as f:
            json.dump({"token": token}, f)
        
        try:
            # Build deploy command
            deploy_cmd = ["vercel", "--prod", "--yes"]
            
            if project_name:
                deploy_cmd.extend(["--name", project_name])
            
            if org_id:
                deploy_cmd.extend(["--scope", org_id])
            
            # Run deploy command
            process = await asyncio.create_subprocess_exec(
                *deploy_cmd,
                cwd=path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            stdout_text = stdout.decode()
            stderr_text = stderr.decode()
            
            if process.returncode != 0:
                logger.error(f"Vercel deployment failed: {stderr_text}")
                raise RuntimeError(f"Vercel deployment failed: {stderr_text}")
            
            # Extract deployment URL
            url_match = re.search(r"Production: (https?://\S+)", stdout_text)
            deployment_url = url_match.group(1) if url_match else ""
            
            logger.info(f"Vercel deployment successful. URL: {deployment_url}")
            
            return {
                "url": deployment_url,
                "logs": stdout_text
            }
            
        except Exception as e:
            logger.error(f"Error deploying to Vercel: {str(e)}")
            raise
        finally:
            # Clean up
            if os.path.exists(creds_path):
                os.remove(creds_path)
    
    async def analyze_logs(self, logs: str) -> List[Dict]:
        """Analyze Vercel deployment logs to identify issues.
        
        Args:
            logs: Deployment logs
            
        Returns:
            List of identified issues
        """
        issues = []
        
        if "Error: Could not authenticate" in logs:
            issues.append({
                "id": "vercel_auth_error",
                "type": "auth_error",
                "message": "Authentication failed. Please check your Vercel token.",
                "severity": "high"
            })
        
        if "Error: No such project" in logs:
            issues.append({
                "id": "vercel_project_not_found",
                "type": "project_error",
                "message": "Project not found. Please check the project name or create a new project.",
                "severity": "high"
            })
        
        if "Error: Build failed" in logs:
            issues.append({
                "id": "vercel_build_error",
                "type": "build_error",
                "message": "Build failed. Check your build configuration.",
                "severity": "high"
            })
        
        if "Error: You do not have access to this organization" in logs:
            issues.append({
                "id": "vercel_org_access_error",
                "type": "auth_error",
                "message": "You don't have access to the specified organization.",
                "severity": "high"
            })
        
        # If no specific issues found but deployment failed
        if not issues and ("error" in logs.lower() or "failed" in logs.lower()):
            issues.append({
                "id": "vercel_unknown_error",
                "type": "unknown_error",
                "message": "Unknown error occurred during deployment. Check the logs for details.",
                "severity": "medium"
            })
        
        return issues