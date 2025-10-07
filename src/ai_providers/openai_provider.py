"""OpenAI provider implementation with function calling support."""

import json
import logging
from typing import Any, Dict, List, Optional, Union

from openai import AsyncOpenAI, OpenAI

from .base import AIProvider, AIResponse, FunctionCall

logger = logging.getLogger(__name__)


class OpenAIProvider(AIProvider):
    """OpenAI provider with support for function calling and reasoning."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize OpenAI provider."""
        super().__init__(config)
        self.api_key = config.get("api_key")
        self.model = config.get("model", "gpt-4o")
        self.base_url = config.get("base_url")

        if not self.api_key:
            raise ValueError("OpenAI API key is required")

        # Initialize both sync and async clients
        client_kwargs = {"api_key": self.api_key}
        if self.base_url:
            client_kwargs["base_url"] = self.base_url

        self.client = OpenAI(**client_kwargs)
        self.async_client = AsyncOpenAI(**client_kwargs)

    @property
    def provider_name(self) -> str:
        """Return the provider name."""
        return "openai"

    @property
    def supported_features(self) -> List[str]:
        """Return supported features."""
        features = ["function_calling", "structured_output"]

        # Check if model supports reasoning
        if self.model in ["gpt-5-mini", "o1-preview", "o1-mini"]:
            features.append("reasoning")

        return features

    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        functions: Optional[List[Dict[str, Any]]] = None,
        function_choice: Optional[Union[str, Dict[str, str]]] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs,
    ) -> AIResponse:
        """Generate response using OpenAI API."""
        try:
            # Prepare request parameters
            request_params = {
                "model": self.model,
                "messages": messages,
                "max_tokens": max_tokens or self.config.get("max_tokens", 4000),
                "temperature": (
                    temperature if temperature is not None else self.config.get("temperature", 0.1)
                ),
            }

            # Add function calling parameters if provided
            if functions:
                if self.supports_feature("function_calling"):
                    request_params["tools"] = [{"type": "function", "function": func} for func in functions]
                    if function_choice:
                        if isinstance(function_choice, str):
                            request_params["tool_choice"] = function_choice
                        else:
                            request_params["tool_choice"] = {
                                "type": "function",
                                "function": function_choice,
                            }
                else:
                    logger.warning(f"Model {self.model} does not support function calling")

            # Handle reasoning models (o1 series)
            if self.supports_feature("reasoning"):
                # o1 models have specific requirements
                request_params.pop("temperature", None)  # o1 doesn't support temperature
                if "reasoning" not in kwargs:
                    request_params["reasoning"] = {
                        "effort": "medium",
                        "summary": "auto",
                    }
                else:
                    request_params["reasoning"] = kwargs["reasoning"]

                # Use responses.create for o1 models
                response = await self.async_client.responses.create(store=False, **request_params)

                return self._parse_reasoning_response(response)
            else:
                # Standard chat completion
                response = await self.async_client.chat.completions.create(**request_params)
                return self._parse_standard_response(response)

        except Exception as e:
            logger.error(f"Error generating OpenAI response: {e}")
            return AIResponse(content=None, function_calls=[], finish_reason="error", usage=None)

    def _parse_standard_response(self, response) -> AIResponse:
        """Parse standard chat completion response."""
        choice = response.choices[0]
        message = choice.message

        function_calls = []
        content = message.content

        # Parse function calls if present
        if hasattr(message, "tool_calls") and message.tool_calls:
            for tool_call in message.tool_calls:
                if tool_call.type == "function":
                    try:
                        arguments = json.loads(tool_call.function.arguments)
                        function_calls.append(
                            FunctionCall(name=tool_call.function.name, arguments=arguments)
                        )
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse function arguments: {e}")
                        continue

        return AIResponse(
            content=content,
            function_calls=function_calls,
            finish_reason=choice.finish_reason,
            usage=response.usage.model_dump() if response.usage else None,
        )

    def _parse_reasoning_response(self, response) -> AIResponse:
        """Parse reasoning model response (o1 series)."""
        function_calls = []
        content = None
        reasoning = None

        for output in response.output:
            if output.type == "function_call":
                try:
                    arguments = json.loads(output.arguments)
                    function_calls.append(FunctionCall(name=output.name, arguments=arguments))
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse function arguments: {e}")
                    continue
            elif output.type == "content":
                content = output.content
            elif output.type == "reasoning":
                reasoning = output.reasoning

        return AIResponse(
            content=content,
            function_calls=function_calls,
            reasoning=reasoning,
            finish_reason=response.finish_reason,
            usage=(response.usage.model_dump() if hasattr(response, "usage") and response.usage else None),
        )

    def validate_connection(self) -> bool:
        """Validate OpenAI API connection."""
        try:
            # Simple API call to validate connection
            response = self.client.models.list()
            return len(list(response)) > 0
        except Exception as e:
            logger.error(f"OpenAI connection validation failed: {e}")
            return False
