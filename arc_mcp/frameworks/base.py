"""Base classes for framework handlers."""

import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional

logger = logging.getLogger("arc-mcp.frameworks.base")

class FrameworkHandler(ABC):
    """Base class for framework-specific deployment handlers."""
    
    @abstractmethod
    async def prepare_for_deployment(self, path: str, provider: str, options: Dict) -> str:
        """Prepare a framework project for deployment.
        
        Args:
            path: Path to the project
            provider: Target hosting provider
            options: Deployment options
            
        Returns:
            Path to the prepared project
        """
        pass
    
    @abstractmethod
    async def get_solutions(self, issues: List[Dict], provider: str) -> List[Dict]:
        """Get framework-specific solutions for deployment issues.
        
        Args:
            issues: List of detected issues
            provider: The hosting provider
            
        Returns:
            List of solution recommendations
        """
        pass
    
    @abstractmethod
    def validate_project(self, path: str) -> Dict:
        """Validate a framework project.
        
        Args:
            path: Path to the project
            
        Returns:
            Validation result with status and issues
        """
        pass