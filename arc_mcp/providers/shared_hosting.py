"""Shared Hosting provider handler for Arc MCP."""

import asyncio
import json
import logging
import os
import re
import subprocess
from typing import Dict, List, Optional
import ftplib
import paramiko

from arc_mcp.providers.base import ProviderHandler

logger = logging.getLogger("arc-mcp.providers.shared_hosting")

class SharedHostingProviderHandler(ProviderHandler):
    """Handler for traditional shared hosting providers."""
    
    async def validate_credentials(self, credentials: Dict[str, str]) -> bool:
        """Validate shared hosting credentials.
        
        Args:
            credentials: Shared hosting credentials
            
        Returns:
            True if credentials are valid, False otherwise
        """
        host = credentials.get("host")
        username = credentials.get("username")
        password = credentials.get("password")
        protocol = credentials.get("protocol", "ftp")
        
        if not all([host, username, password]):
            logger.error("Missing required credentials (host, username, password)")
            return False
        
        try:
            if protocol.lower() == "ftp":
                # Test FTP connection
                with ftplib.FTP(host) as ftp:
                    ftp.login(username, password)
                    logger.info(f"FTP connection successful to {host}")
                    return True
            elif protocol.lower() == "sftp":
                # Test SFTP connection
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(host, username=username, password=password)
                sftp = ssh.open_sftp()
                sftp.close()
                ssh.close()
                logger.info(f"SFTP connection successful to {host}")
                return True
            else:
                logger.error(f"Unsupported protocol: {protocol}")
                return False
        except Exception as e:
            logger.error(f"Error validating shared hosting credentials: {str(e)}")
            return False
    
    async def deploy(self, path: str, credentials: Dict[str, str], options: Dict) -> Dict:
        """Deploy a project to shared hosting.
        
        Args:
            path: Path to the prepared project
            credentials: Shared hosting credentials
            options: Deployment options
            
        Returns:
            Deployment result with URL and other details
        """
        host = credentials.get("host")
        username = credentials.get("username")
        password = credentials.get("password")
        protocol = credentials.get("protocol", "ftp")
        remote_path = options.get("remote_path", "/")
        site_url = options.get("site_url", f"http://{host}")
        
        if not all([host, username, password]):
            raise ValueError("Missing required credentials (host, username, password)")
        
        try:
            if protocol.lower() == "ftp":
                # Deploy via FTP
                await self._deploy_ftp(path, host, username, password, remote_path)
            elif protocol.lower() == "sftp":
                # Deploy via SFTP
                await self._deploy_sftp(path, host, username, password, remote_path)
            else:
                raise ValueError(f"Unsupported protocol: {protocol}")
            
            logger.info(f"Deployment to {host} successful")
            
            return {
                "url": site_url,
                "protocol": protocol,
                "host": host,
                "remote_path": remote_path
            }
        except Exception as e:
            logger.error(f"Error deploying to shared hosting: {str(e)}")
            raise
    
    async def _deploy_ftp(self, local_path, host, username, password, remote_path):
        """Deploy files via FTP."""
        # In a real implementation, this would upload files recursively
        # For simplicity, we're just showing the basic structure
        logger.info(f"Deploying {local_path} to {host}:{remote_path} via FTP")
        # Would implement recursive FTP upload here
    
    async def _deploy_sftp(self, local_path, host, username, password, remote_path):
        """Deploy files via SFTP."""
        # In a real implementation, this would upload files recursively
        # For simplicity, we're just showing the basic structure
        logger.info(f"Deploying {local_path} to {host}:{remote_path} via SFTP")
        # Would implement recursive SFTP upload here
    
    async def analyze_logs(self, logs: str) -> List[Dict]:
        """Analyze shared hosting deployment logs to identify issues.
        
        Args:
            logs: Deployment logs
            
        Returns:
            List of identified issues
        """
        issues = []
        
        if "530 Login incorrect" in logs:
            issues.append({
                "id": "ftp_login_error",
                "type": "auth_error",
                "message": "FTP login failed. Check your username and password.",
                "severity": "high"
            })
        
        if "Connection refused" in logs:
            issues.append({
                "id": "connection_refused",
                "type": "connection_error",
                "message": "Connection refused. Verify the hostname and that the server is accepting connections.",
                "severity": "high"
            })
        
        if "Permission denied" in logs:
            issues.append({
                "id": "permission_denied",
                "type": "permission_error",
                "message": "Permission denied. Check that your user has write access to the remote directory.",
                "severity": "high"
            })
        
        if "No such file" in logs:
            issues.append({
                "id": "no_such_file",
                "type": "path_error",
                "message": "Remote directory does not exist. Verify the remote path.",
                "severity": "medium"
            })
        
        if "Disk quota exceeded" in logs:
            issues.append({
                "id": "quota_exceeded",
                "type": "quota_error",
                "message": "Disk quota exceeded. Free up space or upgrade your hosting plan.",
                "severity": "high"
            })
        
        # If no specific issues found but deployment failed
        if not issues and ("error" in logs.lower() or "failed" in logs.lower()):
            issues.append({
                "id": "shared_hosting_unknown_error",
                "type": "unknown_error",
                "message": "Unknown error occurred during deployment. Check the logs for details.",
                "severity": "medium"
            })
        
        return issues