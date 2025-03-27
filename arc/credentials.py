"""
Secure credential management for Arc MCP Server.
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)

class CredentialManager:
    """
    Manages secure storage and retrieval of credentials for hosting providers.
    """
    
    def __init__(self):
        """Initialize the credential manager."""
        self.credentials_dir = Path.home() / ".arc" / "credentials"
        os.makedirs(self.credentials_dir, exist_ok=True)
        
        # Create or load encryption key
        key_path = self.credentials_dir / ".key"
        if key_path.exists():
            with open(key_path, "rb") as f:
                self.key = f.read()
        else:
            # Generate a new key
            salt = os.urandom(16)
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            self.key = base64.urlsafe_b64encode(kdf.derive(os.urandom(32)))
            with open(key_path, "wb") as f:
                f.write(self.key)
            
            # Secure the key file
            os.chmod(key_path, 0o600)
        
        self.cipher = Fernet(self.key)
        logger.debug("Credential manager initialized")
    
    def store_credentials(self, provider_name: str, credentials: Dict[str, str]) -> bool:
        """
        Store credentials for a hosting provider.
        
        Args:
            provider_name: Name of the hosting provider
            credentials: Dictionary of credentials
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Encrypt credentials
            credentials_json = json.dumps(credentials)
            encrypted_credentials = self.cipher.encrypt(credentials_json.encode())
            
            # Store to file
            cred_file = self.credentials_dir / f"{provider_name}.cred"
            with open(cred_file, "wb") as f:
                f.write(encrypted_credentials)
            
            # Secure the file
            os.chmod(cred_file, 0o600)
            
            logger.info(f"Credentials stored for provider: {provider_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to store credentials: {str(e)}")
            return False
    
    def get_credentials(self, provider_name: str) -> Optional[Dict[str, str]]:
        """
        Retrieve credentials for a hosting provider.
        
        Args:
            provider_name: Name of the hosting provider
            
        Returns:
            Dictionary of credentials if found, None otherwise
        """
        cred_file = self.credentials_dir / f"{provider_name}.cred"
        if not cred_file.exists():
            logger.warning(f"No credentials found for provider: {provider_name}")
            return None
        
        try:
            # Read and decrypt credentials
            with open(cred_file, "rb") as f:
                encrypted_credentials = f.read()
            
            decrypted_data = self.cipher.decrypt(encrypted_credentials)
            credentials = json.loads(decrypted_data.decode())
            
            logger.debug(f"Retrieved credentials for provider: {provider_name}")
            return credentials
        except Exception as e:
            logger.error(f"Failed to retrieve credentials: {str(e)}")
            return None
    
    def delete_credentials(self, provider_name: str) -> bool:
        """
        Delete credentials for a hosting provider.
        
        Args:
            provider_name: Name of the hosting provider
            
        Returns:
            True if successful, False otherwise
        """
        cred_file = self.credentials_dir / f"{provider_name}.cred"
        if not cred_file.exists():
            logger.warning(f"No credentials found for provider: {provider_name}")
            return False
        
        try:
            os.remove(cred_file)
            logger.info(f"Credentials deleted for provider: {provider_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete credentials: {str(e)}")
            return False
