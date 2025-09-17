"""Base AI provider interface for scalable AI model integration."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union


@dataclass
class FunctionCall:
    """Represents a function call made by the AI."""

    name: str
    arguments: Dict[str, Any]


@dataclass
class AIResponse:
    """Standardized response from AI providers."""

    content: Optional[str] = None
    function_calls: List[FunctionCall] = None
    reasoning: Optional[str] = None
    finish_reason: Optional[str] = None
    usage: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.function_calls is None:
            self.function_calls = []


class AIProvider(ABC):
    """Abstract base class for AI providers."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize the AI provider with configuration."""
        self.config = config

    @abstractmethod
    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        functions: Optional[List[Dict[str, Any]]] = None,
        function_choice: Optional[Union[str, Dict[str, str]]] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs,
    ) -> AIResponse:
        """
        Generate a response from the AI model.

        Args:
            messages: List of messages in the conversation
            functions: Optional list of available functions
            function_choice: How the model should choose functions ("auto", "none", or specific function)
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature
            **kwargs: Additional provider-specific parameters

        Returns:
            AIResponse with content and/or function calls
        """
        pass

    @abstractmethod
    def validate_connection(self) -> bool:
        """Validate that the provider connection is working."""
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the name of this AI provider."""
        pass

    @property
    @abstractmethod
    def supported_features(self) -> List[str]:
        """Return list of supported features (e.g., 'function_calling', 'reasoning', 'streaming')."""
        pass

    def supports_feature(self, feature: str) -> bool:
        """Check if the provider supports a specific feature."""
        return feature in self.supported_features
