"""
Tests for the credential manager in Arc MCP.
"""
import unittest
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

from arc.credentials import CredentialManager


class TestCredentialManager(unittest.TestCase):
    """Test cases for the CredentialManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory for credentials
        self.test_dir = tempfile.mkdtemp()
        self.credentials_dir = os.path.join(self.test_dir, "credentials")
        os.makedirs(self.credentials_dir, exist_ok=True)
        
        # Create a CredentialManager with the test directory
        with patch('pathlib.Path.home', return_value=Path(self.test_dir)):
            self.manager = CredentialManager()
    
    def tearDown(self):
        """Tear down test fixtures."""
        shutil.rmtree(self.test_dir)
    
    @patch('builtins.open', new_callable=unittest.mock.mock_open)
    @patch('cryptography.fernet.Fernet.encrypt')
    def test_store_credentials(self, mock_encrypt, mock_open):
        """Test storing credentials."""
        # Setup mocks
        mock_encrypt.return_value = b"encrypted_data"
        
        # Test storing credentials
        credentials = {
            "host": "example.com",
            "username": "user",
            "password": "pass",
            "port": "22",
            "protocol": "sftp"
        }
        
        # Mock the key generation/retrieval
        with patch.object(self.manager, '_get_encryption_key', return_value=b"test_key"):
            self.manager.store_credentials("test_provider", credentials)
        
        # Verify file operations
        mock_open.assert_called_once()
        handle = mock_open()
        handle.write.assert_called_once_with(b"encrypted_data")
        
        # Verify encrypt was called with the correct data
        mock_encrypt.assert_called_once()
        encrypt_args = mock_encrypt.call_args[0][0]
        self.assertIsInstance(encrypt_args, bytes)
        
        # The encrypted data should contain all credential fields
        for key, value in credentials.items():
            self.assertIn(key.encode(), encrypt_args)
            self.assertIn(value.encode(), encrypt_args)
    
    @patch('os.path.exists')
    @patch('builtins.open', new_callable=unittest.mock.mock_open, read_data=b"encrypted_data")
    @patch('cryptography.fernet.Fernet.decrypt')
    def test_get_credentials(self, mock_decrypt, mock_open, mock_exists):
        """Test retrieving credentials."""
        # Setup mocks
        mock_exists.return_value = True
        mock_decrypt.return_value = b'{"host":"example.com","username":"user","password":"pass","port":"22","protocol":"sftp"}'
        
        # Mock the key generation/retrieval
        with patch.object(self.manager, '_get_encryption_key', return_value=b"test_key"):
            credentials = self.manager.get_credentials("test_provider")
        
        # Verify file operations
        mock_open.assert_called_once()
        
        # Verify decrypt was called with the correct data
        mock_decrypt.assert_called_once_with(b"encrypted_data")
        
        # Verify the credentials were correctly decoded
        self.assertEqual(credentials["host"], "example.com")
        self.assertEqual(credentials["username"], "user")
        self.assertEqual(credentials["password"], "pass")
        self.assertEqual(credentials["port"], "22")
        self.assertEqual(credentials["protocol"], "sftp")
    
    @patch('os.path.exists')
    def test_get_credentials_not_found(self, mock_exists):
        """Test retrieving non-existent credentials."""
        # Setup mock
        mock_exists.return_value = False
        
        # Test retrieving non-existent credentials
        credentials = self.manager.get_credentials("non_existent_provider")
        
        # Verify that None is returned
        self.assertIsNone(credentials)
    
    @patch('pathlib.Path.home')
    @patch('os.makedirs')
    def test_get_credentials_directory(self, mock_makedirs, mock_home):
        """Test the _get_credentials_directory method."""
        # Setup mocks
        mock_home.return_value = Path("/home/testuser")
        
        # Call the method
        directory = self.manager._get_credentials_directory()
        
        # Verify the directory path
        self.assertEqual(directory, "/home/testuser/.arc/credentials")
        
        # Verify that makedirs was called with exist_ok=True
        mock_makedirs.assert_called_once_with("/home/testuser/.arc/credentials", exist_ok=True)
    
    @patch('os.urandom')
    @patch('pathlib.Path.home')
    @patch('os.path.exists')
    @patch('builtins.open', new_callable=unittest.mock.mock_open)
    def test_generate_encryption_key(self, mock_open, mock_exists, mock_home, mock_urandom):
        """Test the _generate_encryption_key method."""
        # Setup mocks
        mock_home.return_value = Path("/home/testuser")
        mock_exists.return_value = False
        mock_urandom.return_value = b"random_bytes"
        
        # Call the method
        key = self.manager._generate_encryption_key()
        
        # Verify that urandom was called to generate random bytes
        mock_urandom.assert_called_once_with(32)
        
        # Verify that the key file was created
        mock_open.assert_called_once_with("/home/testuser/.arc/key", "wb")
        handle = mock_open()
        handle.write.assert_called_once()
        
        # Verify that a key was returned
        self.assertIsNotNone(key)
    
    @patch('pathlib.Path.home')
    @patch('os.path.exists')
    @patch('builtins.open', new_callable=unittest.mock.mock_open, read_data=b"existing_key")
    def test_get_encryption_key_existing(self, mock_open, mock_exists, mock_home):
        """Test retrieving an existing encryption key."""
        # Setup mocks
        mock_home.return_value = Path("/home/testuser")
        mock_exists.return_value = True
        
        # Call the method
        key = self.manager._get_encryption_key()
        
        # Verify that the key file was read
        mock_open.assert_called_once_with("/home/testuser/.arc/key", "rb")
        
        # Verify that the correct key was returned
        self.assertEqual(key, b"existing_key")
    
    @patch('pathlib.Path.home')
    @patch('os.path.exists')
    def test_get_encryption_key_not_existing(self, mock_exists, mock_home):
        """Test retrieving a non-existent encryption key."""
        # Setup mocks
        mock_home.return_value = Path("/home/testuser")
        mock_exists.return_value = False
        
        # Mock the key generation
        with patch.object(self.manager, '_generate_encryption_key', return_value=b"new_key") as mock_generate:
            key = self.manager._get_encryption_key()
        
        # Verify that the key generation method was called
        mock_generate.assert_called_once()
        
        # Verify that the correct key was returned
        self.assertEqual(key, b"new_key")


# Run tests if executed directly
if __name__ == '__main__':
    unittest.main()
