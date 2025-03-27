"""
Framework handlers for Arc MCP Server.
"""
from typing import Dict, List, Any, Optional

class FrameworkHandler:
    """Base class for framework handlers."""
    
    name = "base"
    display_name = "Base Framework"
    description = "Base framework handler"
    
    def analyze_requirements(self, project_path: str, provider_name: str) -> Dict[str, Any]:
        """
        Analyze deployment requirements for a framework/provider combination.
        
        Args:
            project_path: Path to the project directory
            provider_name: Name of the hosting provider
            
        Returns:
            Dictionary with requirements analysis
        """
        raise NotImplementedError("Framework handlers must implement analyze_requirements")
    
    def deploy(
        self, 
        project_path: str, 
        provider_name: str, 
        credentials: Dict[str, str],
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Deploy a framework to a hosting provider.
        
        Args:
            project_path: Path to the project directory
            provider_name: Name of the hosting provider
            credentials: Provider credentials
            config: Deployment configuration
            
        Returns:
            Dictionary with deployment results
        """
        raise NotImplementedError("Framework handlers must implement deploy")
    
    def troubleshoot(
        self, 
        project_path: str, 
        provider_name: str,
        error_log: Optional[str]
    ) -> Dict[str, Any]:
        """
        Troubleshoot deployment issues.
        
        Args:
            project_path: Path to the project directory
            provider_name: Name of the hosting provider
            error_log: Optional error log content
            
        Returns:
            Dictionary with troubleshooting results
        """
        raise NotImplementedError("Framework handlers must implement troubleshoot")

# Framework registry
_framework_registry = {}

def register_framework(framework_class):
    """Register a framework handler."""
    _framework_registry[framework_class.name] = framework_class
    return framework_class

def get_framework_handler(framework_name: str) -> Optional[FrameworkHandler]:
    """Get a framework handler by name."""
    if framework_name not in _framework_registry:
        return None
    return _framework_registry[framework_name]()

def list_frameworks() -> List[Dict[str, str]]:
    """List all registered frameworks."""
    return [
        {
            "name": cls.name,
            "display_name": cls.display_name,
            "description": cls.description
        }
        for cls in _framework_registry.values()
    ]
