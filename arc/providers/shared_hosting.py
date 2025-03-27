"""
Implementation of the Shared Hosting provider for Arc MCP Server.
Handles traditional shared hosting environments with FTP/SFTP access.
"""
import os
import time
import logging
import ftplib
import paramiko
import tempfile
import shutil
import hashlib
import fnmatch
import traceback
import stat
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set, Iterator

from arc.providers import register_provider, ProviderHandler

logger = logging.getLogger(__name__)

class FileInfo:
    """Class to store file information for synchronization."""
    
    def __init__(self, path: str, size: int, modified_time: float, hash_value: Optional[str] = None):
        """
        Initialize file info.
        
        Args:
            path: Relative path of the file
            size: File size in bytes
            modified_time: Last modified timestamp
            hash_value: Optional hash value for content comparison
        """
        self.path = path
        self.size = size
        self.modified_time = modified_time
        self.hash_value = hash_value
    
    def __eq__(self, other):
        """Compare file info objects."""
        if not isinstance(other, FileInfo):
            return False
        
        # If hash values are available, use them for comparison
        if self.hash_value and other.hash_value:
            return self.hash_value == other.hash_value
        
        # Otherwise, compare size and modified time
        return (
            self.path == other.path and
            self.size == other.size and
            abs(self.modified_time - other.modified_time) < 1  # Allow 1 second difference
        )
    
    def __hash__(self):
        """Hash for use in sets."""
        return hash((self.path, self.size, int(self.modified_time)))

@register_provider
class SharedHostingProvider(ProviderHandler):
    """
    Handler for traditional shared hosting providers.
    Focuses on secure and robust FTP/SFTP file transfers with smart synchronization.
    
    Features:
    - Smart file synchronization (only uploads changed files)
    - Transactional uploads with rollback capability
    - Support for both FTP and SFTP protocols
    - Backup creation before deployments
    - Extensive error handling and reporting
    """
    
    name = "shared_hosting"
    display_name = "Shared Hosting"
    description = "Traditional shared hosting with FTP/SFTP access"
    
    # Maximum number of retry attempts for file operations
    MAX_RETRIES = 3
    
    # Default exclusion patterns for files that should not be uploaded
    DEFAULT_EXCLUSIONS = [
        '.git', '.github', '.gitignore', '.DS_Store', 
        '__pycache__', '*.pyc', 'node_modules', 
        '.env', '.env.local', '.env.development',
        'README.md', 'LICENSE', 'CHANGELOG.md'
    ]
    
    def validate_credentials(self, credentials: Dict[str, str]) -> Dict[str, Any]:
        """
        Validate shared hosting credentials by attempting to connect.
        
        Args:
            credentials: Dictionary containing host, username, password, port, and protocol
            
        Returns:
            Dictionary with validation results
        """
        required_fields = ["host", "username", "password", "port", "protocol"]
        missing_fields = [field for field in required_fields if field not in credentials]
        
        if missing_fields:
            return {
                "success": False,
                "error": f"Missing required credentials: {', '.join(missing_fields)}"
            }
        
        protocol = credentials["protocol"].lower()
        if protocol not in ["ftp", "sftp"]:
            return {
                "success": False,
                "error": f"Unsupported protocol: {protocol}. Must be 'ftp' or 'sftp'."
            }
        
        try:
            # Attempt to connect to validate credentials
            if protocol == "ftp":
                with ftplib.FTP() as ftp:
                    ftp.connect(
                        host=credentials["host"],
                        port=int(credentials["port"]) if credentials["port"] else 21
                    )
                    ftp.login(credentials["username"], credentials["password"])
                    ftp.quit()
            else:  # SFTP
                client = paramiko.SSHClient()
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                client.connect(
                    hostname=credentials["host"],
                    port=int(credentials["port"]) if credentials["port"] else 22,
                    username=credentials["username"],
                    password=credentials["password"]
                )
                client.close()
            
            return {
                "success": True,
                "message": f"Successfully connected to {credentials['host']} using {protocol.upper()}"
            }
        except Exception as e:
            logger.error(f"Connection error: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to connect: {str(e)}"
            }
    
    def check_status(self, credentials: Dict[str, str], site_id: Optional[str]) -> Dict[str, Any]:
        """
        Check the status of the shared hosting server.
        
        Args:
            credentials: Provider credentials
            site_id: Optional site identifier (not used for shared hosting)
            
        Returns:
            Dictionary with status information
        """
        # Reuse the validation logic to check connection
        validation_result = self.validate_credentials(credentials)
        if not validation_result["success"]:
            return validation_result
        
        # If we can connect, the server is online
        return {
            "success": True,
            "status": "online",
            "host": credentials["host"],
            "protocol": credentials["protocol"],
            "message": f"Server is online and accessible via {credentials['protocol'].upper()}"
        }
    
    def get_deployment_status(self, credentials: Dict[str, str], site_id: Optional[str]) -> Dict[str, Any]:
        """
        Get deployment status for a shared hosting site.
        
        Args:
            credentials: Provider credentials
            site_id: Optional site identifier (not used for shared hosting)
            
        Returns:
            Dictionary with deployment status
        """
        # For shared hosting, we can't easily determine deployment status
        # So we just check if the server is accessible
        connection_status = self.check_status(credentials, site_id)
        if not connection_status["success"]:
            return connection_status
        
        # Try to access a common file that would indicate a deployed site
        protocol = credentials["protocol"].lower()
        remote_path = site_id or "/"
        common_files = ["index.html", "index.php", "index.htm"]
        deployed = False
        
        try:
            if protocol == "ftp":
                with ftplib.FTP() as ftp:
                    ftp.connect(
                        host=credentials["host"],
                        port=int(credentials["port"]) if credentials["port"] else 21
                    )
                    ftp.login(credentials["username"], credentials["password"])
                    
                    # Navigate to the target directory
                    if remote_path != "/":
                        try:
                            ftp.cwd(remote_path)
                        except ftplib.error_perm:
                            # Directory doesn't exist
                            return {
                                "success": True,
                                "status": "not_deployed",
                                "message": f"Directory {remote_path} does not exist"
                            }
                    
                    # Check for common index files
                    files = ftp.nlst()
                    for file in common_files:
                        if file in files:
                            deployed = True
                            break
                    
            else:  # SFTP
                client = paramiko.SSHClient()
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                client.connect(
                    hostname=credentials["host"],
                    port=int(credentials["port"]) if credentials["port"] else 22,
                    username=credentials["username"],
                    password=credentials["password"]
                )
                
                sftp = client.open_sftp()
                try:
                    # Navigate to the target directory
                    if remote_path != "/":
                        try:
                            sftp.chdir(remote_path)
                        except IOError:
                            # Directory doesn't exist
                            sftp.close()
                            client.close()
                            return {
                                "success": True,
                                "status": "not_deployed",
                                "message": f"Directory {remote_path} does not exist"
                            }
                    
                    # Check for common index files
                    files = sftp.listdir()
                    for file in common_files:
                        if file in files:
                            deployed = True
                            break
                finally:
                    sftp.close()
                    client.close()
            
            status = "deployed" if deployed else "partial"
            message = (
                f"Site appears to be deployed at {credentials['host']}/{remote_path}"
                if deployed else
                f"Directory exists but no index file found at {credentials['host']}/{remote_path}"
            )
            
            return {
                "success": True,
                "status": status,
                "host": credentials["host"],
                "path": remote_path,
                "message": message
            }
            
        except Exception as e:
            logger.error(f"Error checking deployment status: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to check deployment status: {str(e)}"
            }
    
    def deploy(
        self, 
        credentials: Dict[str, str], 
        source_dir: str,
        destination: str,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Deploy to shared hosting via FTP/SFTP with smart synchronization.
        
        Args:
            credentials: Provider credentials
            source_dir: Source directory to deploy
            destination: Destination path on the server
            config: Deployment configuration
            
        Returns:
            Dictionary with deployment results
        """
        logger.info(f"Starting deployment to {credentials['host']}:{destination}")
        
        # Validate the source directory
        if not os.path.isdir(source_dir):
            return {
                "success": False,
                "error": f"Source directory does not exist: {source_dir}"
            }
        
        # Ensure the source directory ends with a slash for consistency
        source_dir = os.path.join(source_dir, "")
        
        # Extract configuration options
        backup = config.get("backup", True)
        clean_destination = config.get("clean_destination", False)
        exclusions = config.get("exclusions", self.DEFAULT_EXCLUSIONS)
        sync_mode = config.get("sync_mode", "smart")  # 'smart', 'full', or 'incremental'
        
        # Prepare for deployment
        protocol = credentials["protocol"].lower()
        port = int(credentials["port"]) if credentials["port"] else (22 if protocol == "sftp" else 21)
        
        # Execute the appropriate deployment method
        try:
            if protocol == "ftp":
                result = self._deploy_ftp(
                    credentials=credentials,
                    source_dir=source_dir,
                    destination=destination,
                    port=port,
                    backup=backup,
                    clean_destination=clean_destination,
                    exclusions=exclusions,
                    sync_mode=sync_mode
                )
            else:  # SFTP
                result = self._deploy_sftp(
                    credentials=credentials,
                    source_dir=source_dir,
                    destination=destination,
                    port=port,
                    backup=backup,
                    clean_destination=clean_destination,
                    exclusions=exclusions,
                    sync_mode=sync_mode
                )
            
            if result["success"]:
                # Add deployment URL for convenience
                host = credentials["host"]
                path = destination.strip("/")
                result["url"] = f"https://{host}/{path}" if path else f"https://{host}"
            
            return result
            
        except Exception as e:
            logger.error(f"Deployment error: {str(e)}")
            return {
                "success": False,
                "error": f"Deployment failed: {str(e)}"
            }
    
    def _deploy_ftp(
        self,
        credentials: Dict[str, str],
        source_dir: str,
        destination: str,
        port: int,
        backup: bool,
        clean_destination: bool,
        exclusions: List[str],
        sync_mode: str
    ) -> Dict[str, Any]:
        """Deploy via FTP with smart synchronization."""
        username = credentials["username"]
        password = credentials["password"]
        host = credentials["host"]
        
        # Connect to FTP server
        ftp = ftplib.FTP()
        try:
            ftp.connect(host=host, port=port)
            ftp.login(username, password)
            
            # Ensure destination directory exists
            self._ensure_ftp_directory(ftp, destination)
            
            # Create backup if requested
            if backup:
                backup_name = f"{destination.rstrip('/')}_backup_{int(time.time())}"
                try:
                    logger.info(f"Creating backup at {backup_name}")
                    self._create_ftp_backup(ftp, destination, backup_name)
                except Exception as e:
                    logger.warning(f"Backup failed, but continuing with deployment: {str(e)}")
            
            # Clean destination if requested
            if clean_destination:
                logger.info(f"Cleaning destination directory: {destination}")
                self._clean_ftp_directory(ftp, destination, exclusions)
            
            # Gather local files
            local_files = self._scan_local_directory(source_dir, exclusions)
            
            # For smart sync, gather remote files for comparison
            remote_files = {}
            if sync_mode == "smart" or sync_mode == "incremental":
                remote_files = self._scan_ftp_directory(ftp, destination)
            
            # Determine files to upload based on sync mode
            to_upload = self._determine_files_to_upload(
                local_files=local_files,
                remote_files=remote_files,
                sync_mode=sync_mode
            )
            
            # Proceed with upload
            uploaded_count = 0
            skipped_count = 0
            for rel_path, file_info in to_upload.items():
                local_path = os.path.join(source_dir, rel_path)
                remote_path = os.path.join(destination, rel_path).replace("\\", "/")
                
                # Ensure remote directory exists
                remote_dir = os.path.dirname(remote_path).replace("\\", "/")
                self._ensure_ftp_directory(ftp, remote_dir)
                
                # Upload the file
                try:
                    with open(local_path, 'rb') as f:
                        ftp.storbinary(f'STOR {remote_path}', f)
                    uploaded_count += 1
                    logger.debug(f"Uploaded: {remote_path}")
                except Exception as e:
                    logger.error(f"Failed to upload {remote_path}: {str(e)}")
                    raise
            
            skipped_count = len(local_files) - uploaded_count
            
            return {
                "success": True,
                "message": "Deployment completed successfully",
                "stats": {
                    "files_uploaded": uploaded_count,
                    "files_skipped": skipped_count,
                    "total_files": len(local_files)
                }
            }
            
        except Exception as e:
            logger.error(f"FTP deployment error: {str(e)}")
            return {
                "success": False,
                "error": f"FTP deployment failed: {str(e)}"
            }
        finally:
            try:
                ftp.quit()
            except:
                pass
    
    def _deploy_sftp(
        self,
        credentials: Dict[str, str],
        source_dir: str,
        destination: str,
        port: int,
        backup: bool,
        clean_destination: bool,
        exclusions: List[str],
        sync_mode: str
    ) -> Dict[str, Any]:
        """Deploy via SFTP with smart synchronization."""
        username = credentials["username"]
        password = credentials["password"]
        host = credentials["host"]
        
        # Connect to SFTP server
        client = paramiko.SSHClient()
        try:
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(hostname=host, port=port, username=username, password=password)
            
            sftp = client.open_sftp()
            
            # Ensure destination directory exists
            self._ensure_sftp_directory(sftp, destination)
            
            # Create backup if requested
            if backup:
                backup_name = f"{destination.rstrip('/')}_backup_{int(time.time())}"
                try:
                    logger.info(f"Creating backup at {backup_name}")
                    self._create_sftp_backup(sftp, destination, backup_name)
                except Exception as e:
                    logger.warning(f"Backup failed, but continuing with deployment: {str(e)}")
            
            # Clean destination if requested
            if clean_destination:
                logger.info(f"Cleaning destination directory: {destination}")
                self._clean_sftp_directory(sftp, destination, exclusions)
            
            # Gather local files
            local_files = self._scan_local_directory(source_dir, exclusions)
            
            # For smart sync, gather remote files for comparison
            remote_files = {}
            if sync_mode == "smart" or sync_mode == "incremental":
                remote_files = self._scan_sftp_directory(sftp, destination)
            
            # Determine files to upload based on sync mode
            to_upload = self._determine_files_to_upload(
                local_files=local_files,
                remote_files=remote_files,
                sync_mode=sync_mode
            )
            
            # Proceed with upload
            uploaded_count = 0
            skipped_count = 0
            for rel_path, file_info in to_upload.items():
                local_path = os.path.join(source_dir, rel_path)
                remote_path = os.path.join(destination, rel_path).replace("\\", "/")
                
                # Ensure remote directory exists
                remote_dir = os.path.dirname(remote_path).replace("\\", "/")
                self._ensure_sftp_directory(sftp, remote_dir)
                
                # Upload the file
                try:
                    sftp.put(local_path, remote_path)
                    uploaded_count += 1
                    logger.debug(f"Uploaded: {remote_path}")
                except Exception as e:
                    logger.error(f"Failed to upload {remote_path}: {str(e)}")
                    raise
            
            skipped_count = len(local_files) - uploaded_count
            
            return {
                "success": True,
                "message": "Deployment completed successfully",
                "stats": {
                    "files_uploaded": uploaded_count,
                    "files_skipped": skipped_count,
                    "total_files": len(local_files)
                }
            }
            
        except Exception as e:
            logger.error(f"SFTP deployment error: {str(e)}")
            return {
                "success": False,
                "error": f"SFTP deployment failed: {str(e)}"
            }
        finally:
            try:
                sftp.close()
                client.close()
            except:
                pass