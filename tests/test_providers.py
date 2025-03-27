"""
Tests for the provider handlers in Arc MCP.
"""
import unittest
import os
import tempfile
import shutil
from unittest.mock import patch, MagicMock, mock_open

from arc.providers import ProviderHandler, get_provider_handler, list_providers
from arc.providers.shared_hosting import SharedHostingProvider, FileInfo


class TestProviderBase(unittest.TestCase):
    """Test cases for the base ProviderHandler class."""
    
    def test_provider_handler_abstract(self):
        """Test that ProviderHandler is effectively abstract."""
        handler = ProviderHandler()
        
        with self.assertRaises(NotImplementedError):
            handler.validate_credentials({})
        
        with self.assertRaises(NotImplementedError):
            handler.check_status({}, None)
        
        with self.assertRaises(NotImplementedError):
            handler.get_deployment_status({}, None)
        
        with self.assertRaises(NotImplementedError):
            handler.deploy({}, "", "", {})


class TestFileInfo(unittest.TestCase):
    """Test cases for the FileInfo class."""
    
    def test_file_info_equality(self):
        """Test FileInfo equality comparison."""
        # Create two FileInfo objects with same attributes
        file1 = FileInfo("path/to/file.txt", 1024, 1600000000, "abcdef")
        file2 = FileInfo("path/to/file.txt", 1024, 1600000000, "abcdef")
        
        # They should be equal
        self.assertEqual(file1, file2)
        
        # Create a FileInfo with different hash
        file3 = FileInfo("path/to/file.txt", 1024, 1600000000, "123456")
        
        # They should not be equal
        self.assertNotEqual(file1, file3)
        
        # Create a FileInfo with same size and close timestamp but no hash
        file4 = FileInfo("path/to/file.txt", 1024, 1600000000.5)
        file5 = FileInfo("path/to/file.txt", 1024, 1600000000.8)
        
        # They should be considered equal due to close timestamps
        self.assertEqual(file4, file5)
        
        # Create a FileInfo with different size
        file6 = FileInfo("path/to/file.txt", 2048, 1600000000)
        
        # They should not be equal
        self.assertNotEqual(file4, file6)


class TestSharedHostingProvider(unittest.TestCase):
    """Test cases for the SharedHostingProvider class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.provider = SharedHostingProvider()
        
        # Create temporary directory for test files
        self.test_dir = tempfile.mkdtemp()
        
        # Create some test files
        test_files = [
            "index.html",
            "css/style.css",
            "js/script.js",
            "images/logo.png"
        ]
        
        for file_path in test_files:
            full_path = os.path.join(self.test_dir, file_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'w') as f:
                f.write(f"Content of {file_path}")
    
    def tearDown(self):
        """Tear down test fixtures."""
        shutil.rmtree(self.test_dir)
    
    def test_validate_credentials_missing_fields(self):
        """Test validate_credentials with missing fields."""
        # Missing required fields
        credentials = {
            "host": "example.com",
            "username": "user"
            # Missing password, port, protocol
        }
        
        result = self.provider.validate_credentials(credentials)
        
        self.assertFalse(result["success"])
        self.assertIn("Missing required credentials", result["error"])
    
    def test_validate_credentials_invalid_protocol(self):
        """Test validate_credentials with invalid protocol."""
        # Invalid protocol
        credentials = {
            "host": "example.com",
            "username": "user",
            "password": "pass",
            "port": "22",
            "protocol": "invalid"  # Not ftp or sftp
        }
        
        result = self.provider.validate_credentials(credentials)
        
        self.assertFalse(result["success"])
        self.assertIn("Unsupported protocol", result["error"])
    
    @patch('ftplib.FTP')
    def test_validate_credentials_ftp_success(self, mock_ftp):
        """Test successful FTP credential validation."""
        # Setup mock
        mock_ftp_instance = MagicMock()
        mock_ftp.return_value.__enter__.return_value = mock_ftp_instance
        
        # Valid FTP credentials
        credentials = {
            "host": "example.com",
            "username": "user",
            "password": "pass",
            "port": "21",
            "protocol": "ftp"
        }
        
        result = self.provider.validate_credentials(credentials)
        
        self.assertTrue(result["success"])
        mock_ftp_instance.connect.assert_called_once_with(host="example.com", port=21)
        mock_ftp_instance.login.assert_called_once_with("user", "pass")
        mock_ftp_instance.quit.assert_called_once()
    
    @patch('paramiko.SSHClient')
    def test_validate_credentials_sftp_success(self, mock_ssh):
        """Test successful SFTP credential validation."""
        # Setup mock
        mock_ssh_instance = MagicMock()
        mock_ssh.return_value = mock_ssh_instance
        
        # Valid SFTP credentials
        credentials = {
            "host": "example.com",
            "username": "user",
            "password": "pass",
            "port": "22",
            "protocol": "sftp"
        }
        
        result = self.provider.validate_credentials(credentials)
        
        self.assertTrue(result["success"])
        mock_ssh_instance.set_missing_host_key_policy.assert_called_once()
        mock_ssh_instance.connect.assert_called_once_with(
            hostname="example.com", port=22, username="user", password="pass"
        )
        mock_ssh_instance.close.assert_called_once()
    
    def test_scan_local_directory(self):
        """Test _scan_local_directory method."""
        # Scan the test directory
        files = self.provider._scan_local_directory(self.test_dir, [])
        
        # Check that all files were found
        self.assertIn("index.html", files)
        self.assertIn("css/style.css", files)
        self.assertIn("js/script.js", files)
        self.assertIn("images/logo.png", files)
        
        # Check that each entry is a FileInfo object
        for file_info in files.values():
            self.assertIsInstance(file_info, FileInfo)
            self.assertTrue(hasattr(file_info, 'path'))
            self.assertTrue(hasattr(file_info, 'size'))
            self.assertTrue(hasattr(file_info, 'modified_time'))
            self.assertTrue(hasattr(file_info, 'hash_value'))
    
    def test_determine_files_to_upload_full_sync(self):
        """Test _determine_files_to_upload with 'full' sync mode."""
        # Create local files
        local_files = {
            "file1.txt": FileInfo("file1.txt", 100, 1600000000, "abc"),
            "file2.txt": FileInfo("file2.txt", 200, 1600000000, "def")
        }
        
        # Create remote files
        remote_files = {
            "file1.txt": FileInfo("file1.txt", 100, 1600000000),
            "file3.txt": FileInfo("file3.txt", 300, 1600000000)
        }
        
        # Test full sync (should upload all local files)
        to_upload = self.provider._determine_files_to_upload(
            local_files=local_files,
            remote_files=remote_files,
            sync_mode="full"
        )
        
        # Check that all local files are in to_upload
        self.assertEqual(len(to_upload), len(local_files))
        self.assertIn("file1.txt", to_upload)
        self.assertIn("file2.txt", to_upload)
    
    def test_determine_files_to_upload_incremental_sync(self):
        """Test _determine_files_to_upload with 'incremental' sync mode."""
        # Create local files
        local_files = {
            "file1.txt": FileInfo("file1.txt", 100, 1600000000, "abc"),
            "file2.txt": FileInfo("file2.txt", 200, 1600000000, "def")
        }
        
        # Create remote files
        remote_files = {
            "file1.txt": FileInfo("file1.txt", 100, 1600000000),
            "file3.txt": FileInfo("file3.txt", 300, 1600000000)
        }
        
        # Test incremental sync (should upload only new files)
        to_upload = self.provider._determine_files_to_upload(
            local_files=local_files,
            remote_files=remote_files,
            sync_mode="incremental"
        )
        
        # Check that only new files are in to_upload
        self.assertEqual(len(to_upload), 1)
        self.assertNotIn("file1.txt", to_upload)  # Already exists remotely
        self.assertIn("file2.txt", to_upload)     # New file
    
    def test_determine_files_to_upload_smart_sync(self):
        """Test _determine_files_to_upload with 'smart' sync mode."""
        # Create local files
        local_files = {
            "file1.txt": FileInfo("file1.txt", 100, 1600000000, "abc"),  # Same as remote
            "file2.txt": FileInfo("file2.txt", 200, 1600000100, "def"),  # New file
            "file3.txt": FileInfo("file3.txt", 150, 1600000000, "xyz")   # Modified file (different size)
        }
        
        # Create remote files
        remote_files = {
            "file1.txt": FileInfo("file1.txt", 100, 1600000000),  # Same as local
            "file3.txt": FileInfo("file3.txt", 300, 1600000000),  # Different size
            "file4.txt": FileInfo("file4.txt", 400, 1600000000)   # Remote only
        }
        
        # Test smart sync (should upload new and modified files)
        to_upload = self.provider._determine_files_to_upload(
            local_files=local_files,
            remote_files=remote_files,
            sync_mode="smart"
        )
        
        # Check that new and modified files are in to_upload
        self.assertEqual(len(to_upload), 2)
        self.assertNotIn("file1.txt", to_upload)  # Unchanged
        self.assertIn("file2.txt", to_upload)     # New file
        self.assertIn("file3.txt", to_upload)     # Modified file


# Run tests if executed directly
if __name__ == '__main__':
    unittest.main()
