"""Function calling schemas for AI agents to interact with context tools."""

# flake8: noqa: E501
from typing import Any, Dict, List


def get_context_tool_schemas() -> List[Dict[str, Any]]:
    """Get all function schemas for context tools."""
    return [
        get_file_content_schema(),
        search_codebase_schema(),
        find_function_definition_schema(),
        find_class_definition_schema(),
        find_import_usages_schema(),
        find_test_files_schema(),
    ]


def get_file_content_schema() -> Dict[str, Any]:
    """Schema for getting file content."""
    return {
        "name": "get_file_content",
        "description": "Get the content of a specific file from the repository, optionally limited to specific line ranges. Use this when you need to examine specific files mentioned in the diff or related files.",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path to the file in the repository (e.g., 'src/models.py')",
                },
                "start_line": {
                    "type": "integer",
                    "description": "Starting line number (1-based, inclusive). Optional - omit to get entire file.",
                    "minimum": 1,
                },
                "end_line": {
                    "type": "integer",
                    "description": "Ending line number (1-based, inclusive). Optional - omit to get from start_line to end of file.",
                    "minimum": 1,
                },
            },
            "required": ["file_path"],
            "additionalProperties": False,
        },
    }


def search_codebase_schema() -> Dict[str, Any]:
    """Schema for searching the codebase."""
    return {
        "name": "search_codebase",
        "description": "Search the entire codebase for specific patterns, function names, class names, or text. Use this to find where symbols are defined or used across the project.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query - can be a function name, class name, variable, or any text pattern you want to find",
                },
                "file_extension": {
                    "type": "string",
                    "description": "Limit search to files with specific extension (e.g., '.py', '.js', '.ts'). Optional.",
                    "pattern": "^\\.[a-zA-Z0-9]+$",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results to return. Defaults to 20.",
                    "minimum": 1,
                    "maximum": 50,
                    "default": 20,
                },
            },
            "required": ["query"],
            "additionalProperties": False,
        },
    }


def find_function_definition_schema() -> Dict[str, Any]:
    """Schema for finding function definitions."""
    return {
        "name": "find_function_definition",
        "description": "Find the complete definition of a specific function. Use this when you see a function call in the diff and want to understand what the function does, its parameters, or implementation details.",
        "parameters": {
            "type": "object",
            "properties": {
                "function_name": {
                    "type": "string",
                    "description": "Name of the function to find the definition for",
                },
                "file_path": {
                    "type": "string",
                    "description": "Specific file to search in. Optional - if omitted, searches across entire codebase.",
                },
            },
            "required": ["function_name"],
            "additionalProperties": False,
        },
    }


def find_class_definition_schema() -> Dict[str, Any]:
    """Schema for finding class definitions."""
    return {
        "name": "find_class_definition",
        "description": "Find the complete definition of a specific class including its methods and attributes. Use this when you see class usage in the diff and want to understand the class structure, inheritance, or interface.",
        "parameters": {
            "type": "object",
            "properties": {
                "class_name": {
                    "type": "string",
                    "description": "Name of the class to find the definition for",
                },
                "file_path": {
                    "type": "string",
                    "description": "Specific file to search in. Optional - if omitted, searches across entire codebase.",
                },
            },
            "required": ["class_name"],
            "additionalProperties": False,
        },
    }


def find_import_usages_schema() -> Dict[str, Any]:
    """Schema for finding import usages."""
    return {
        "name": "find_import_usages",
        "description": "Find all files that import a specific module. Use this to understand the impact of changes to a module - which other files might be affected.",
        "parameters": {
            "type": "object",
            "properties": {
                "module_name": {
                    "type": "string",
                    "description": "Name of the module to find imports for (e.g., 'os', 'requests', 'myproject.utils')",
                }
            },
            "required": ["module_name"],
            "additionalProperties": False,
        },
    }


def find_test_files_schema() -> Dict[str, Any]:
    """Schema for finding test files."""
    return {
        "name": "find_test_files",
        "description": "Find test files related to a source file. Use this to check if changes might break existing tests or if new functionality needs tests.",
        "parameters": {
            "type": "object",
            "properties": {
                "source_file": {
                    "type": "string",
                    "description": "Path to the source file to find tests for (e.g., 'src/models.py')",
                }
            },
            "required": ["source_file"],
            "additionalProperties": False,
        },
    }


def get_review_analysis_schema() -> Dict[str, Any]:
    """Schema for the final review analysis function."""
    return {
        "name": "create_review_analysis",
        "description": "Create the final structured code review analysis after gathering all necessary context. Call this when you have sufficient information to provide a comprehensive review.",
        "parameters": {
            "type": "object",
            "properties": {
                "issues": {
                    "type": "array",
                    "description": "List of specific issues found in the code changes",
                    "items": {
                        "type": "object",
                        "properties": {
                            "title": {
                                "type": "string",
                                "description": "Brief title describing the issue",
                            },
                            "description": {
                                "type": "string",
                                "description": "Detailed description of the issue and why it's problematic",
                            },
                            "severity": {
                                "type": "string",
                                "enum": ["critical", "high", "medium", "low", "info"],
                                "description": "Severity level of the issue",
                            },
                            "change_type": {
                                "type": "string",
                                "enum": [
                                    "bug",
                                    "performance",
                                    "security",
                                    "memory",
                                    "error_handling",
                                ],
                                "description": "Type of issue identified",
                            },
                            "target_lines": {
                                "type": "array",
                                "description": "Line numbers from the diff that this issue applies to",
                                "items": {"type": "integer"},
                            },
                            "suggestion": {
                                "type": ["string", "null"],
                                "description": "Suggested fix or improvement (code only, no explanations)",
                            },
                            "side": {
                                "type": "string",
                                "enum": ["LEFT", "RIGHT"],
                                "description": "Which side of the diff this issue applies to. LEFT for deleted/old code, RIGHT for added/new code",
                            },
                            "context_used": {
                                "type": "array",
                                "description": "List of context sources that informed this issue (e.g., related files examined)",
                                "items": {"type": "string"},
                            },
                        },
                        "required": [
                            "title",
                            "description",
                            "severity",
                            "change_type",
                            "target_lines",
                            "suggestion",
                            "side",
                        ],
                        "additionalProperties": False,
                    },
                },
                "overall_assessment": {
                    "type": "string",
                    "description": "Overall assessment of the code changes including context-aware insights",
                },
                "context_summary": {
                    "type": "string",
                    "description": "Summary of what additional context was gathered and how it influenced the review",
                },
            },
            "required": ["issues", "overall_assessment", "context_summary"],
            "additionalProperties": False,
        },
    }
