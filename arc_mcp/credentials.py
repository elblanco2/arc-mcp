"""Secure credential management for Arc MCP Server."""

import json
import logging
import os
from pathlib import Path
from typing import Dict, Optional

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    import base64
except ImportError:
    print("Cryptography package not found. Please install with 'pip install cryptography'")

logger = logging.getLogger("arc-mcp.credentials")

class CredentialsManager:
    """Secure storage and retrieval of provider credentials."""
    
    def __init__(self, storage_path: str = "~/.arc/credentials"):
        """Initialize the credentials manager.
        
        Args:
            storage_path: Path to store the encrypted credentials file
        """
        self.storage_path = os.path.expanduser(storage_path)
        self._ensure_storage_dir()
        
        # Generate or retrieve encryption key
        self.key = self._get_encryption_key()
        self.cipher = Fernet(self.key)
        
        # Cache for credentials
        self._credentials_cache = {}
        
        # Load existing credentials
        self._load_credentials()
    
    def _ensure_storage_dir(self):
        """Ensure the storage directory exists."""
        storage_dir = os.path.dirname(self.storage_path)
        os.makedirs(storage_dir, exist_ok=True)
        
        # Set secure permissions on the directory
        try:
            os.chmod(storage_dir, 0o700)  # Only user can access
        except Exception as e:
            logger.warning(f"Could not set secure permissions on {storage_dir}: {str(e)}")
    
    def _get_encryption_key(self) -> bytes:
        """Get or generate the encryption key."""
        key_path = os.path.join(os.path.dirname(self.storage_path), ".key")
        
        # If key exists, use it
        if os.path.exists(key_path):
            with open(key_path, "rb") as key_file:
                return key_file.read()
        
        # Generate a new key
        key = Fernet.generate_key()
        
        # Save the key
        with open(key_path, "wb") as key_file:
            key_file.write(key)
        
        # Set secure permissions
        try:
            os.chmod(key_path, 0o600)  # Only user can read
        except Exception as e:
            logger.warning(f"Could not set secure permissions on {key_path}: {str(e)}")
            
        return key
    
    def _load_credentials(self):
        """Load credentials from the storage file."""
        if not os.path.exists(self.storage_path):
            # No credentials file yet
            return
        
        try:
            with open(self.storage_path, "rb") as f:
                encrypted_data = f.read()
                if encrypted_data:
                    decrypted_data = self.cipher.decrypt(encrypted_data)
                    self._credentials_cache = json.loads(decrypted_data.decode("utf-8"))
        except Exception as e:
            logger.error(f"Error loading credentials: {str(e)}")
            # Start with empty credentials on error
            self._credentials_cache = {}
    
    def _save_credentials_to_disk(self):
        """Save credentials to the storage file."""
        try:
            data = json.dumps(self._credentials_cache).encode("utf-8")
            encrypted_data = self.cipher.encrypt(data)
            
            with open(self.storage_path, "wb") as f:
                f.write(encrypted_data)
                
            # Set secure permissions
            try:
                os.chmod(self.storage_path, 0o600)  # Only user can read
            except Exception as e:
                logger.warning(f"Could not set secure permissions on {self.storage_path}: {str(e)}")
        except Exception as e:
            logger.error(f"Error saving credentials: {str(e)}")
            raise
    
    def save_credentials(self, provider: str, credentials: Dict[str, str]):
        """Save credentials for a provider.
        
        Args:
            provider: Provider name
            credentials: Dictionary of credentials
        """
        self._credentials_cache[provider] = credentials
        self._save_credentials_to_disk()
        logger.info(f"Saved credentials for provider: {provider}")
    
    def get_credentials(self, provider: str) -> Optional[Dict[str, str]]:
        """Get credentials for a provider.
        
        Args:
            provider: Provider name
            
        Returns:
            Dictionary of credentials or None if not found
        """
        return self._credentials_cache.get(provider)
    
    def delete_credentials(self, provider: str) -> bool:
        """Delete credentials for a provider.
        
        Args:
            provider: Provider name
            
        Returns:
            True if credentials were deleted, False if not found
        """
        if provider in self._credentials_cache:
            del self._credentials_cache[provider]
            self._save_credentials_to_disk()
            logger.info(f"Deleted credentials for provider: {provider}")
            return True
        return False
    
    def list_providers(self) -> list:
        """List all providers with saved credentials.
        
        Returns:
            List of provider names
        """
        return list(self._credentials_cache.keys())
