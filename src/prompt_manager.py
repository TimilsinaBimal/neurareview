"""Prompt management for NeuraReview."""

import logging
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class PromptManager:
    """Manages loading and formatting of prompts for different review modes."""

    def __init__(self):
        """Initialize the prompt manager."""
        self.prompts_dir = Path(__file__).parent / "prompts"
        self._prompt_cache: Dict[str, str] = {}

    def get_agentic_system_prompt(self) -> str:
        """Get the system prompt for agentic review mode."""
        return self._load_prompt("agentic_system_prompt.md")

    def get_traditional_review_prompt(self, language: str = "Python") -> str:
        """Get traditional review prompt with language formatting."""
        prompt_template = self._load_prompt("traditional_review_prompt.md")
        return prompt_template.format(language=language)

    def _load_prompt(self, filename: str) -> str:
        """Load a prompt from file with caching."""
        if filename in self._prompt_cache:
            return self._prompt_cache[filename]

        prompt_path = self.prompts_dir / filename

        try:
            with open(prompt_path, "r", encoding="utf-8") as f:
                content = f.read()

            self._prompt_cache[filename] = content
            logger.debug(f"Loaded prompt from {prompt_path}")
            return content

        except FileNotFoundError:
            logger.error(f"Prompt file not found: {prompt_path}")
            return self._get_fallback_prompt(filename)
        except Exception as e:
            logger.error(f"Error loading prompt from {prompt_path}: {e}")
            return self._get_fallback_prompt(filename)

    def _get_fallback_prompt(self, filename: str) -> str:
        """Get fallback prompt when file loading fails."""
        if "agentic" in filename:
            return self._get_agentic_fallback()
        else:
            return self._get_traditional_fallback()

    def _get_agentic_fallback(self) -> str:
        """Fallback prompt for agentic review mode."""
        return """You are an expert code reviewer with the ability to gather additional
        context about the codebase.

Your goal is to provide thorough, context-aware code reviews by:
1. First analyzing the provided code changes
2. Deciding if you need more context to provide a quality review
3. Using available tools to gather additional information
4. Providing comprehensive feedback based on all available information

Available tools:
- get_file_content: Get content of specific files
- search_codebase: Search for patterns, functions, classes across codebase
- find_function_definition: Find complete function definitions
- find_class_definition: Find complete class definitions
- find_import_usages: Find files that import specific modules
- find_test_files: Find test files for source files

When you have gathered enough context, call create_review_analysis with your final assessment."""

    def _get_traditional_fallback(self) -> str:
        """Fallback prompt for traditional review mode."""
        return """You are an expert code reviewer focused on critical issues only.

Focus on:
- Security vulnerabilities
- Memory issues
- Performance problems
- Critical bugs
- Error handling

Only report issues that could cause real problems in production."""

    def reload_prompts(self) -> None:
        """Clear the prompt cache to force reloading from files."""
        self._prompt_cache.clear()
        logger.info("Prompt cache cleared - prompts will be reloaded")

    def list_available_prompts(self) -> list[str]:
        """List all available prompt files."""
        if not self.prompts_dir.exists():
            return []

        return [f.name for f in self.prompts_dir.glob("*.md")]

    def add_custom_prompt(self, name: str, content: str) -> None:
        """Add a custom prompt to the cache (not saved to file)."""
        self._prompt_cache[name] = content
        logger.info(f"Added custom prompt: {name}")

    def get_custom_prompt(self, name: str) -> Optional[str]:
        """Get a custom prompt by name."""
        return self._prompt_cache.get(name)
