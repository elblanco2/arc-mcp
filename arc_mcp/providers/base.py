"""Base classes for provider handlers."""

import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional

logger = logging.getLogger("arc-mcp.providers.base")

class ProviderHandler(ABC):
    """Base class for hosting provider deployment handlers."""
    
    @abstractmethod
    async def validate_credentials(self, credentials: Dict[str, str]) -> bool:
        """Validate provider credentials.
        
        Args:
            credentials: Provider credentials
            
        Returns:
            True if credentials are valid, False otherwise
        """
        pass
    
    @abstractmethod
    async def deploy(self, path: str, credentials: Dict[str, str], options: Dict) -> Dict:
        """Deploy a project to the provider.
        
        Args:
            path: Path to the prepared project
            credentials: Provider credentials
            options: Deployment options
            
        Returns:
            Deployment result with URL and other details
        """
        pass
    
    @abstractmethod
    async def analyze_logs(self, logs: str) -> List[Dict]:
        """Analyze deployment logs to identify issues.
        
        Args:
            logs: Deployment logs
            
        Returns:
            List of identified issues
        """
        pass