"""
Purpose: Base class for AI client implementations.

Why: Provide a common interface for different AI providers, enabling
easy switching or support for multiple providers.

How: Define abstract methods that all AI clients must implement.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, Optional


class BaseAIClient(ABC):
    """Base class for AI client implementations.
    
    All AI clients should inherit from this class and implement
    the abstract methods.
    """
    
    @abstractmethod
    def summarize(self, text: str, *, title: Optional[str] = None) -> str:
        """Generate a summary for the given text.
        
        Args:
            text: Text to summarize (can be URL or content)
            title: Optional title to improve summary quality
            
        Returns:
            Summary string
        """
        raise NotImplementedError
    
    @abstractmethod
    def analyze(self, data: Dict) -> Dict:
        """Analyze data and return insights.
        
        Args:
            data: Data dictionary to analyze
            
        Returns:
            Analysis results dictionary
        """
        raise NotImplementedError
    
    @abstractmethod
    def generate_response(self, prompt: str, context: Optional[str] = None) -> str:
        """Generate a response based on prompt and optional context.
        
        Args:
            prompt: User prompt or question
            context: Optional context to provide additional information
            
        Returns:
            Generated response string
        """
        raise NotImplementedError
