# Arc MCP Testing Guide

This guide covers how to install, set up, and run tests for the Arc MCP server.

## Table of Contents

- [Installation](#installation)
- [Running Tests](#running-tests)
- [Test Structure](#test-structure)
- [Writing New Tests](#writing-new-tests)
- [CI/CD Integration](#cicd-integration)
- [Debugging Tests](#debugging-tests)

## Installation

### Prerequisites

Before you can test Arc MCP, make sure you have:

- Python 3.8 or higher
- pip (Python package manager)
- Git

### Install for Testing

1. Clone the repository:

```bash
git clone https://github.com/elblanco2/arc-mcp.git
cd arc-mcp
```

2. Install the package in development mode with testing dependencies:

```bash
pip install -e ".[dev]"
```

This command installs:
- Arc MCP in development mode (`-e`), so changes to the code take effect immediately
- All the required testing dependencies (pytest, pytest-cov, etc.)

## Running Tests

### Basic Test Run

To run all tests:

```bash
pytest
```

### With Coverage Report

To run tests with coverage reporting:

```bash
pytest --cov=arc
```

This is the default when running pytest, thanks to our configuration in `pytest.ini`.

### Running Specific Tests

To run a specific test file:

```bash
pytest tests/test_server.py
```

To run a specific test class:

```bash
pytest tests/test_server.py::TestArcServer
```

To run a specific test method:

```bash
pytest tests/test_server.py::TestArcServer::test_server_initialization
```

### Test Output Options

For more detailed output:

```bash
pytest -v  # verbose
pytest -xvs  # verbose, stop on first failure, no capture
```

## Test Structure

The Arc MCP test suite is organized into several files:

- **test_server.py**: Tests for the main MCP server functionality
- **test_frameworks.py**: Tests for framework handlers (Wasp, etc.)
- **test_providers.py**: Tests for provider handlers (shared hosting, etc.)
- **test_credentials.py**: Tests for the credential management system

Each test file corresponds to a core component of the Arc MCP system.

## Writing New Tests

When writing new tests, follow these guidelines:

1. **Naming Convention**:
   - Test files should be named `test_*.py`
   - Test classes should be named `Test*`
   - Test methods should be named `test_*`

2. **Test Organization**:
   - Group related tests in classes
   - Use descriptive method names
   - Add docstrings to explain test purpose

3. **Use Fixtures**:
   - Use `setUp` and `tearDown` methods for common setup/cleanup
   - Create temporary files and directories in `setUp` and clean them in `tearDown`

4. **Mocking External Dependencies**:
   - Use `unittest.mock` for external dependencies
   - Mock file operations, network connections, etc.
   - Avoid making actual network calls in tests

5. **Testing Pattern**:
   - Arrange: Set up the test conditions
   - Act: Execute the function being tested
   - Assert: Verify the results match expectations

### Example Test Structure

```python
class TestFeature(unittest.TestCase):
    def setUp(self):
        # Common setup
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        # Common cleanup
        shutil.rmtree(self.temp_dir)
    
    def test_function_success(self):
        """Test that function works with valid input."""
        # Arrange
        input_data = {"key": "value"}
        
        # Act
        result = function_to_test(input_data)
        
        # Assert
        self.assertTrue(result["success"])
        self.assertEqual(result["message"], "Expected message")
    
    def test_function_failure(self):
        """Test that function handles invalid input."""
        # Arrange
        invalid_input = {}
        
        # Act
        result = function_to_test(invalid_input)
        
        # Assert
        self.assertFalse(result["success"])
        self.assertIn("error", result)
```

## CI/CD Integration

Testing is integrated into the CI/CD pipeline through GitHub Actions. The workflow is defined in `.github/workflows/tests.yml`.

The CI/CD pipeline:
1. Runs on multiple Python versions (3.8, 3.9, 3.10)
2. Installs dependencies
3. Runs tests with coverage
4. Reports test results
5. Fails the build if any tests fail

## Debugging Tests

### Common Issues

1. **Module Not Found Errors**:
   - Make sure you've installed the package in development mode
   - Check your import paths

2. **Permission Errors**:
   - Some tests create temporary files and directories
   - Ensure your user has permission to write to the temp directory

3. **Mock Issues**:
   - Verify that you're mocking the correct path
   - Check that mock return values match expected formats

### Debugging Techniques

1. **Print Debugging**:
   - Add `print()` statements to your tests
   - Run pytest with `-s` flag to see print output

2. **Debug with pdb**:
   - Add `import pdb; pdb.set_trace()` where you want to pause execution
   - Run pytest with `--no-header --no-summary -xvs` for cleaner debug output

3. **Isolate Failing Tests**:
   - Run only the failing test to focus debugging
   - Add more assertions to pinpoint where the issue occurs

4. **Check Test Coverage**:
   - Review the coverage report to find untested code paths
   - Add tests for missing coverage areas

## Additional Resources

- [PyTest Documentation](https://docs.pytest.org/)
- [Python unittest Documentation](https://docs.python.org/3/library/unittest.html)
- [Mock Object Library](https://docs.python.org/3/library/unittest.mock.html)
