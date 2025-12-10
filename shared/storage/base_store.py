"""
Purpose: Base storage interface for data persistence.

Why: Provide a common interface for different storage implementations,
enabling easy switching between in-memory, file-based, or database storage.

How: Define abstract methods that all storage implementations must implement.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any


class BaseStore(ABC):
    """Base class for storage implementations.
    
    All storage implementations should inherit from this class and implement
    the abstract methods.
    """
    
    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """Get a value by key.
        
        Args:
            key: Storage key
            
        Returns:
            Stored value or None if not found
        """
        raise NotImplementedError
    
    @abstractmethod
    def set(self, key: str, value: Any) -> bool:
        """Set a value by key.
        
        Args:
            key: Storage key
            value: Value to store
            
        Returns:
            True if successful, False otherwise
        """
        raise NotImplementedError
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete a value by key.
        
        Args:
            key: Storage key
            
        Returns:
            True if successful, False otherwise
        """
        raise NotImplementedError
    
    @abstractmethod
    def list_all(self) -> List[Any]:
        """List all stored values.
        
        Returns:
            List of all stored values
        """
        raise NotImplementedError
    
    @abstractmethod
    def clear(self) -> bool:
        """Clear all stored values.
        
        Returns:
            True if successful, False otherwise
        """
        raise NotImplementedError
