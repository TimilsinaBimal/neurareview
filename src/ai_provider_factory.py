"""Factory for creating AI providers."""

import logging

from .ai_providers.base import AIProvider
from .ai_providers.openai_provider import OpenAIProvider
from .config import AIConfig

# from typing import Dict, Any


logger = logging.getLogger(__name__)


class AIProviderFactory:
    """Factory for creating AI provider instances."""

    _providers = {
        "openai": OpenAIProvider,
        # Add more providers here as they're implemented
        # "anthropic": AnthropicProvider,
        # "google": GoogleProvider,
        # "azure": AzureOpenAIProvider,
    }

    @classmethod
    def create_provider(cls, config: AIConfig) -> AIProvider:
        """
        Create an AI provider instance based on configuration.

        Args:
            config: AI configuration

        Returns:
            AIProvider instance

        Raises:
            ValueError: If provider is not supported
        """
        provider_name = config.provider.lower()

        if provider_name not in cls._providers:
            available = ", ".join(cls._providers.keys())
            raise ValueError(
                f"Unsupported AI provider: {provider_name}. " f"Available providers: {available}"
            )

        provider_class = cls._providers[provider_name]
        provider_config = config.to_provider_config()

        logger.info(f"Creating {provider_name} provider with model {config.model}")

        try:
            return provider_class(provider_config)
        except Exception as e:
            logger.error(f"Failed to create {provider_name} provider: {e}")
            raise

    @classmethod
    def get_supported_providers(cls) -> list[str]:
        """Get list of supported provider names."""
        return list(cls._providers.keys())

    @classmethod
    def register_provider(cls, name: str, provider_class: type) -> None:
        """
        Register a new AI provider.

        Args:
            name: Provider name
            provider_class: Provider class that implements AIProvider
        """
        if not issubclass(provider_class, AIProvider):
            raise ValueError("Provider class must inherit from AIProvider")

        cls._providers[name.lower()] = provider_class
        logger.info("Registered new AI provider: %s", name)
