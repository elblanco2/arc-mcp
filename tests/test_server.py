"""
Tests for the Arc MCP server functionality.
"""
import unittest
import asyncio
from unittest.mock import patch, MagicMock

from arc.server import ArcServer


class TestArcServer(unittest.TestCase):
    """Test cases for the ArcServer class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create server with testing mode enabled
        self.server = ArcServer(debug=True)
    
    def tearDown(self):
        """Tear down test fixtures."""
        self.server = None
    
    def test_server_initialization(self):
        """Test that the server initializes properly."""
        self.assertEqual(self.server.name, "arc")
        self.assertEqual(self.server.description, "Arc MCP Server - Simplified web application deployment")
        self.assertTrue(self.server.debug)
        self.assertIsNotNone(self.server.credential_manager)
    
    @patch('arc.server.get_framework_handler')
    def test_analyze_requirements_tool(self, mock_get_framework):
        """Test the analyze_requirements tool."""
        # Setup mock
        mock_framework = MagicMock()
        mock_framework.analyze_requirements.return_value = {
            "success": True,
            "framework": "wasp",
            "provider": "shared_hosting",
            "app_name": "test-app",
            "requirements": {
                "node_version": ">=14.0.0",
                "build_command": "wasp build",
                "output_dir": ".wasp/build/web-app",
                "environment_variables": ["DATABASE_URL", "JWT_SECRET"],
                "uses_database": True
            }
        }
        mock_get_framework.return_value = mock_framework
        
        # Test with mocks
        with patch('os.path.isdir', return_value=True):
            result = self.server._tool_analyze_requirements("wasp", "shared_hosting", "/fake/path")
            
            # Verify results
            self.assertTrue(result["success"])
            self.assertEqual(result["framework"], "wasp")
            self.assertEqual(result["provider"], "shared_hosting")
            mock_framework.analyze_requirements.assert_called_once_with("/fake/path", "shared_hosting")
    
    @patch('arc.server.get_provider_handler')
    def test_authenticate_provider_tool(self, mock_get_provider):
        """Test the authenticate_provider tool."""
        # Setup mock
        mock_provider = MagicMock()
        mock_provider.validate_credentials.return_value = {
            "success": True,
            "message": "Successfully connected"
        }
        mock_get_provider.return_value = mock_provider
        
        # Test with mocks
        with patch.object(self.server.credential_manager, 'store_credentials') as mock_store:
            credentials = {
                "host": "example.com",
                "username": "testuser",
                "password": "testpass",
                "port": "22",
                "protocol": "sftp"
            }
            result = self.server._tool_authenticate_provider("shared_hosting", credentials)
            
            # Verify results
            self.assertTrue(result["success"])
            self.assertEqual(result["provider"], "shared_hosting")
            mock_provider.validate_credentials.assert_called_once_with(credentials)
            mock_store.assert_called_once_with("shared_hosting", credentials)


# Run tests if executed directly
if __name__ == '__main__':
    unittest.main()
