"""
Tests for the framework handlers in Arc MCP.
"""
import unittest
import os
import tempfile
import shutil
from unittest.mock import patch, MagicMock, mock_open

from arc.frameworks import FrameworkHandler, get_framework_handler, list_frameworks
from arc.frameworks.wasp import WaspFrameworkHandler


class TestFrameworkBase(unittest.TestCase):
    """Test cases for the base FrameworkHandler class."""
    
    def test_framework_handler_abstract(self):
        """Test that FrameworkHandler is effectively abstract."""
        handler = FrameworkHandler()
        
        with self.assertRaises(NotImplementedError):
            handler.analyze_requirements("path", "provider")
        
        with self.assertRaises(NotImplementedError):
            handler.deploy("path", "provider", {}, {})
        
        with self.assertRaises(NotImplementedError):
            handler.troubleshoot("path", "provider", None)


class TestWaspFrameworkHandler(unittest.TestCase):
    """Test cases for the WaspFrameworkHandler class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.handler = WaspFrameworkHandler()
        
        # Create temporary directory for test files
        self.test_dir = tempfile.mkdtemp()
        
        # Create a mock .wasp file
        wasp_content = """
        app TestApp {
          title: "Test Application",
          db: postgresql
        }
        """
        
        self.wasp_file = os.path.join(self.test_dir, "main.wasp")
        with open(self.wasp_file, 'w') as f:
            f.write(wasp_content)
        
        # Create a mock .env.example file
        env_example_content = """
        # Required environment variables
        DATABASE_URL=postgres://user:pass@localhost:5432/db
        JWT_SECRET=your-secret-key
        # Optional environment variables
        LOG_LEVEL=info
        """
        
        env_example_file = os.path.join(self.test_dir, ".env.example")
        with open(env_example_file, 'w') as f:
            f.write(env_example_content)
    
    def tearDown(self):
        """Tear down test fixtures."""
        shutil.rmtree(self.test_dir)
    
    def test_find_wasp_file(self):
        """Test the _find_wasp_file method."""
        # Test finding an existing .wasp file
        wasp_file = self.handler._find_wasp_file(self.test_dir)
        self.assertEqual(wasp_file, self.wasp_file)
        
        # Test with a directory that doesn't have a .wasp file
        empty_dir = tempfile.mkdtemp()
        try:
            wasp_file = self.handler._find_wasp_file(empty_dir)
            self.assertIsNone(wasp_file)
        finally:
            shutil.rmtree(empty_dir)
    
    def test_extract_app_name(self):
        """Test the _extract_app_name method."""
        # Test with a valid .wasp file content
        with open(self.wasp_file, 'r') as f:
            wasp_content = f.read()
        
        app_name = self.handler._extract_app_name(wasp_content)
        self.assertEqual(app_name, "TestApp")
        
        # Test with a .wasp file without app name
        app_name = self.handler._extract_app_name("// This is a comment")
        self.assertIsNone(app_name)
    
    @patch('os.path.isdir')
    @patch('arc.providers.get_provider_handler')
    def test_analyze_requirements(self, mock_get_provider, mock_isdir):
        """Test the analyze_requirements method."""
        # Setup mocks
        mock_provider = MagicMock()
        mock_provider.get_capabilities.return_value = {
            "database_support": True
        }
        mock_get_provider.return_value = mock_provider
        mock_isdir.return_value = True
        
        # Test the analyze_requirements method
        result = self.handler.analyze_requirements(self.test_dir, "shared_hosting")
        
        # Verify results
        self.assertTrue(result["success"])
        self.assertEqual(result["framework"], "wasp")
        self.assertEqual(result["provider"], "shared_hosting")
        self.assertEqual(result["app_name"], "TestApp")
        self.assertTrue(result["requirements"]["uses_database"])
        self.assertEqual(result["requirements"]["node_version"], ">=14.0.0")
        self.assertEqual(result["requirements"]["build_command"], "wasp build")
        
        # Verify environment variables are detected
        env_vars = result["requirements"]["environment_variables"]
        self.assertIn("DATABASE_URL", env_vars)
        self.assertIn("JWT_SECRET", env_vars)
        self.assertIn("LOG_LEVEL", env_vars)
    
    @patch('subprocess.Popen')
    def test_build_project(self, mock_popen):
        """Test the _build_project method."""
        # Setup mock
        process_mock = MagicMock()
        process_mock.returncode = 0
        process_mock.communicate.return_value = ("Build succeeded", "")
        mock_popen.return_value = process_mock
        
        # Setup temporary build output directory
        build_dir = os.path.join(self.test_dir, ".wasp/build/web-app")
        os.makedirs(build_dir)
        
        # Test the build process
        with patch('os.path.exists', return_value=True), \
             patch('shutil.copytree') as mock_copytree:
            
            result = self.handler._build_project(
                self.test_dir, 
                tempfile.mkdtemp(), 
                {"env": {"DATABASE_URL": "test-url"}}
            )
            
            # Verify results
            self.assertTrue(result["success"])
            self.assertIn("output_dir", result)
            self.assertEqual(result["message"], "Build completed successfully")
            
            # Verify subprocess was called correctly
            mock_popen.assert_called_once()
            args, kwargs = mock_popen.call_args
            self.assertEqual(kwargs["cwd"], self.test_dir)
            
            # Verify environment variables were passed
            self.assertIn("DATABASE_URL", kwargs["env"])
            self.assertEqual(kwargs["env"]["DATABASE_URL"], "test-url")
            
            # Verify build output was copied
            mock_copytree.assert_called_once()


# Run tests if executed directly
if __name__ == '__main__':
    unittest.main()
