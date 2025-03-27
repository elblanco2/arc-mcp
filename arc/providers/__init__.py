"""
Hosting provider handlers for Arc MCP Server.
"""
from typing import Dict, List, Any, Optional

class ProviderHandler:
    """Base class for hosting provider handlers."""
    
    name = "base"
    display_name = "Base Provider"
    description = "Base hosting provider handler"
    
    def validate_credentials(self, credentials: Dict[str, str]) -> Dict[str, Any]:
        """
        Validate credentials for a hosting provider.
        
        Args:
            credentials: Dictionary of credentials
            
        Returns:
            Dictionary with validation results
        """
        raise NotImplementedError("Provider handlers must implement validate_credentials")
    
    def check_status(self, credentials: Dict[str, str], site_id: Optional[str]) -> Dict[str, Any]:
        """
        Check the status of a hosting provider.
        
        Args:
            credentials: Provider credentials
            site_id: Optional site identifier
            
        Returns:
            Dictionary with status information
        """
        raise NotImplementedError("Provider handlers must implement check_status")
    
    def get_deployment_status(self, credentials: Dict[str, str], site_id: Optional[str]) -> Dict[str, Any]:
        """
        Get the deployment status.
        
        Args:
            credentials: Provider credentials
            site_id: Optional site identifier
            
        Returns:
            Dictionary with deployment status
        """
        raise NotImplementedError("Provider handlers must implement get_deployment_status")
    
    def deploy(
        self, 
        credentials: Dict[str, str], 
        source_dir: str,
        destination: str,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Deploy to a hosting provider.
        
        Args:
            credentials: Provider credentials
            source_dir: Source directory to deploy
            destination: Destination path or identifier
            config: Deployment configuration
            
        Returns:
            Dictionary with deployment results
        """
        raise NotImplementedError("Provider handlers must implement deploy")
    
    def get_capabilities(self) -> Dict[str, bool]:
        """
        Get the capabilities of the provider.
        
        Returns:
            Dictionary of capability names to boolean values
        """
        return {
            "database_support": False,
            "custom_domain": False,
            "ssl": False,
            "cdn": False,
            "serverless_functions": False
        }
    
    def get_troubleshooting_info(self, framework_name: Optional[str] = None) -> Dict[str, List[str]]:
        """
        Get troubleshooting information for the provider.
        
        Args:
            framework_name: Optional framework name to get specific information
            
        Returns:
            Dictionary with issues and recommendations
        """
        return {
            "issues": [],
            "recommendations": []
        }

# Provider registry
_provider_registry = {}

def register_provider(provider_class):
    """Register a provider handler."""
    _provider_registry[provider_class.name] = provider_class
    return provider_class

def get_provider_handler(provider_name: str) -> Optional[ProviderHandler]:
    """Get a provider handler by name."""
    if provider_name not in _provider_registry:
        return None
    return _provider_registry[provider_name]()

def list_providers() -> List[Dict[str, str]]:
    """List all registered providers."""
    return [
        {
            "name": cls.name,
            "display_name": cls.display_name,
            "description": cls.description
        }
        for cls in _provider_registry.values()
    ]
