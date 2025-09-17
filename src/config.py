"""Configuration management for NeuraReview."""

import os
from dataclasses import dataclass
from typing import List


@dataclass
class GitHubConfig:
    """GitHub API configuration."""

    token: str
    api_url: str = "https://api.github.com"


@dataclass
class AIConfig:
    """AI service configuration."""

    provider: str = "openai"
    model: str = "gpt-4.1"
    api_key: str = ""
    max_tokens: int = 4000
    temperature: float = 0.1


@dataclass
class ReviewConfig:
    """Review behavior configuration."""

    max_files_per_pr: int = 50
    skip_file_types: List[str] = None
    focus_areas: List[str] = None
    min_confidence: float = 0.7

    def __post_init__(self):
        if self.skip_file_types is None:
            self.skip_file_types = [
                ".md",
                ".txt",
                ".json",
                ".yml",
                ".yaml",
                ".xml",
                ".lock",
                ".gitignore",
                ".gitattributes",
                ".env",
                ".log",
                ".csv",
                ".sql",
                ".png",
                ".jpg",
                ".jpeg",
                ".gif",
                ".svg",
                ".ico",
                ".woff",
                ".woff2",
                ".ttf",
            ]
        if self.focus_areas is None:
            self.focus_areas = ["security", "performance", "quality", "bugs"]


@dataclass
class Config:
    """Main configuration class."""

    github: GitHubConfig
    ai: AIConfig
    review: ReviewConfig

    @classmethod
    def from_env(cls) -> "Config":
        """Create configuration from environment variables."""
        github_token = os.getenv("GITHUB_TOKEN")
        if not github_token:
            raise ValueError("GITHUB_TOKEN environment variable is required")

        openai_key = os.getenv("OPENAI_API_KEY")
        if not openai_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")

        return cls(
            github=GitHubConfig(token=github_token),
            ai=AIConfig(api_key=openai_key),
            review=ReviewConfig(),
        )
