"""Context gathering tool for agentic code review."""

import ast
import logging
import re
from typing import Dict, List, Optional, Union

from github.GithubException import GithubException

from .github_client import GitHubClient
from .models import PRData

logger = logging.getLogger(__name__)


class ContextTool:
    """Tool that provides AI agents with the ability to gather additional context from the codebase."""

    def __init__(self, github_client: GitHubClient, pr_data: PRData):
        """Initialize context tool with GitHub client and PR data."""
        self.github_client = github_client
        self.pr_data = pr_data
        self.repo = github_client.get_repository(pr_data.repository)
        self._file_cache: Dict[str, str] = {}
        self._search_cache: Dict[str, List[Dict]] = {}

    def get_file_content(
        self,
        file_path: str,
        start_line: Optional[int] = None,
        end_line: Optional[int] = None,
    ) -> Dict[str, Union[str, bool]]:
        """
        Get content of a specific file, optionally limited to specific lines.

        Args:
            file_path: Path to the file in the repository
            start_line: Starting line number (1-based, inclusive)
            end_line: Ending line number (1-based, inclusive)

        Returns:
            Dict with 'content', 'success', and optional 'error' keys
        """
        try:
            # Check cache first
            cache_key = f"{file_path}:{start_line}:{end_line}"
            if cache_key in self._file_cache:
                return {"content": self._file_cache[cache_key], "success": True}

            # Fetch file from GitHub
            try:
                file_obj = self.repo.get_contents(file_path, ref=self.pr_data.head_sha)
                if file_obj.type != "file":
                    return {
                        "content": "",
                        "success": False,
                        "error": "Path is not a file",
                    }

                content = file_obj.decoded_content.decode("utf-8")
            except GithubException as e:
                if e.status == 404:
                    return {"content": "", "success": False, "error": "File not found"}
                raise

            # Extract specific lines if requested
            if start_line is not None or end_line is not None:
                lines = content.split("\n")
                start_idx = (start_line - 1) if start_line is not None else 0
                end_idx = end_line if end_line is not None else len(lines)
                content = "\n".join(lines[start_idx:end_idx])

            # Cache the result
            self._file_cache[cache_key] = content

            return {"content": content, "success": True}

        except Exception as e:
            logger.error(f"Error getting file content for {file_path}: {e}")
            return {"content": "", "success": False, "error": str(e)}

    def search_codebase(
        self, query: str, file_extension: Optional[str] = None, max_results: int = 20
    ) -> Dict[str, Union[List[Dict], bool]]:
        """
        Search the codebase for specific patterns or text.

        Args:
            query: Search query (can be regex pattern)
            file_extension: Limit search to specific file extension (e.g., ".py")
            max_results: Maximum number of results to return

        Returns:
            Dict with 'results', 'success', and optional 'error' keys
        """
        try:
            cache_key = f"{query}:{file_extension}:{max_results}"
            if cache_key in self._search_cache:
                return {"results": self._search_cache[cache_key], "success": True}

            # Use GitHub search API
            search_query = f'"{query}" repo:{self.pr_data.repository}'
            if file_extension:
                search_query += f" extension:{file_extension.lstrip('.')}"

            search_results = self.github_client.github.search_code(query=search_query, sort="indexed")

            results = []
            count = 0
            for item in search_results:
                if count >= max_results:
                    break

                # Get a snippet around the match
                try:
                    file_content = self.get_file_content(item.path)
                    if file_content["success"]:
                        snippet = self._extract_snippet_around_match(file_content["content"], query)
                        results.append(
                            {
                                "file_path": item.path,
                                "snippet": snippet,
                                "url": item.html_url,
                            }
                        )
                        count += 1
                except Exception as e:
                    logger.warning(f"Error processing search result {item.path}: {e}")
                    continue

            self._search_cache[cache_key] = results
            return {"results": results, "success": True}

        except Exception as e:
            logger.error(f"Error searching codebase for '{query}': {e}")
            return {"results": [], "success": False, "error": str(e)}

    def find_function_definition(
        self, function_name: str, file_path: Optional[str] = None
    ) -> Dict[str, Union[str, bool]]:
        """
        Find the definition of a specific function.

        Args:
            function_name: Name of the function to find
            file_path: Specific file to search in (optional)

        Returns:
            Dict with 'definition', 'file_path', 'success', and optional 'error' keys
        """
        try:
            if file_path:
                # Search in specific file
                file_content = self.get_file_content(file_path)
                if not file_content["success"]:
                    return {
                        "definition": "",
                        "file_path": "",
                        "success": False,
                        "error": file_content.get("error", "Unknown error"),
                    }

                definition = self._extract_function_definition(file_content["content"], function_name)
                if definition:
                    return {
                        "definition": definition,
                        "file_path": file_path,
                        "success": True,
                    }
            else:
                # Search across codebase
                search_results = self.search_codebase(f"def {function_name}", ".py", 5)
                if search_results["success"]:
                    for result in search_results["results"]:
                        file_content = self.get_file_content(result["file_path"])
                        if file_content["success"]:
                            definition = self._extract_function_definition(
                                file_content["content"], function_name
                            )
                            if definition:
                                return {
                                    "definition": definition,
                                    "file_path": result["file_path"],
                                    "success": True,
                                }

            return {
                "definition": "",
                "file_path": "",
                "success": False,
                "error": f"Function '{function_name}' not found",
            }

        except Exception as e:
            logger.error(f"Error finding function definition for '{function_name}': {e}")
            return {
                "definition": "",
                "file_path": "",
                "success": False,
                "error": str(e),
            }

    def find_class_definition(
        self, class_name: str, file_path: Optional[str] = None
    ) -> Dict[str, Union[str, bool]]:
        """
        Find the definition of a specific class.

        Args:
            class_name: Name of the class to find
            file_path: Specific file to search in (optional)

        Returns:
            Dict with 'definition', 'file_path', 'success', and optional 'error' keys
        """
        try:
            if file_path:
                # Search in specific file
                file_content = self.get_file_content(file_path)
                if not file_content["success"]:
                    return {
                        "definition": "",
                        "file_path": "",
                        "success": False,
                        "error": file_content.get("error", "Unknown error"),
                    }

                definition = self._extract_class_definition(file_content["content"], class_name)
                if definition:
                    return {
                        "definition": definition,
                        "file_path": file_path,
                        "success": True,
                    }
            else:
                # Search across codebase
                search_results = self.search_codebase(f"class {class_name}", ".py", 5)
                if search_results["success"]:
                    for result in search_results["results"]:
                        file_content = self.get_file_content(result["file_path"])
                        if file_content["success"]:
                            definition = self._extract_class_definition(file_content["content"], class_name)
                            if definition:
                                return {
                                    "definition": definition,
                                    "file_path": result["file_path"],
                                    "success": True,
                                }

            return {
                "definition": "",
                "file_path": "",
                "success": False,
                "error": f"Class '{class_name}' not found",
            }

        except Exception as e:
            logger.error(f"Error finding class definition for '{class_name}': {e}")
            return {
                "definition": "",
                "file_path": "",
                "success": False,
                "error": str(e),
            }

    def find_import_usages(self, module_name: str) -> Dict[str, Union[List[Dict], bool]]:
        """
        Find files that import a specific module.

        Args:
            module_name: Name of the module to find imports for

        Returns:
            Dict with 'usages', 'success', and optional 'error' keys
        """
        try:
            # Search for various import patterns
            import_patterns = [
                f"import {module_name}",
                f"from {module_name}",
                f"import.*{module_name}",
            ]

            all_usages = []
            for pattern in import_patterns:
                search_results = self.search_codebase(pattern, ".py", 10)
                if search_results["success"]:
                    all_usages.extend(search_results["results"])

            # Remove duplicates based on file_path
            seen_files = set()
            unique_usages = []
            for usage in all_usages:
                if usage["file_path"] not in seen_files:
                    seen_files.add(usage["file_path"])
                    unique_usages.append(usage)

            return {"usages": unique_usages, "success": True}

        except Exception as e:
            logger.error(f"Error finding import usages for '{module_name}': {e}")
            return {"usages": [], "success": False, "error": str(e)}

    def find_test_files(self, source_file: str) -> Dict[str, Union[List[str], bool]]:
        """
        Find test files related to a source file.

        Args:
            source_file: Path to the source file

        Returns:
            Dict with 'test_files', 'success', and optional 'error' keys
        """
        try:
            # Extract base name and create test file patterns
            base_name = source_file.replace(".py", "").replace("/", "_").replace("\\", "_")
            test_patterns = [
                f"test_{base_name}",
                f"{base_name}_test",
                f"test{base_name}",
                base_name.split("/")[-1] if "/" in base_name else base_name,
            ]

            test_files = []
            for pattern in test_patterns:
                search_results = self.search_codebase(pattern, ".py", 5)
                if search_results["success"]:
                    for result in search_results["results"]:
                        if "test" in result["file_path"].lower():
                            test_files.append(result["file_path"])

            # Remove duplicates
            test_files = list(set(test_files))

            return {"test_files": test_files, "success": True}

        except Exception as e:
            logger.error(f"Error finding test files for '{source_file}': {e}")
            return {"test_files": [], "success": False, "error": str(e)}

    def _extract_snippet_around_match(self, content: str, query: str, context_lines: int = 3) -> str:
        """Extract a snippet of code around a search match."""
        lines = content.split("\n")

        # Find the line containing the query
        match_line = -1
        for i, line in enumerate(lines):
            if re.search(re.escape(query), line, re.IGNORECASE):
                match_line = i
                break

        if match_line == -1:
            return content[:200] + "..." if len(content) > 200 else content

        # Extract context around the match
        start = max(0, match_line - context_lines)
        end = min(len(lines), match_line + context_lines + 1)

        snippet_lines = []
        for i in range(start, end):
            prefix = ">>> " if i == match_line else "    "
            snippet_lines.append(f"{prefix}{i+1:4d}: {lines[i]}")

        return "\n".join(snippet_lines)

    def _extract_function_definition(self, content: str, function_name: str) -> str:
        """Extract function definition from file content."""
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name == function_name:
                    lines = content.split("\n")
                    start_line = node.lineno - 1

                    # Find the end of the function (next function/class or end of file)
                    end_line = len(lines)
                    for other_node in ast.walk(tree):
                        if (
                            isinstance(other_node, (ast.FunctionDef, ast.ClassDef))
                            and other_node.lineno > node.lineno
                        ):
                            end_line = min(end_line, other_node.lineno - 1)

                    # Limit to first 20 lines of the function to avoid huge definitions
                    end_line = min(end_line, start_line + 20)

                    return "\n".join(lines[start_line:end_line])

            return ""
        except SyntaxError:
            # Fallback to regex if AST parsing fails
            pattern = rf"def\s+{re.escape(function_name)}\s*\([^)]*\):"
            lines = content.split("\n")
            for i, line in enumerate(lines):
                if re.search(pattern, line):
                    # Return the function signature and first few lines
                    end_idx = min(len(lines), i + 10)
                    return "\n".join(lines[i:end_idx])
            return ""

    def _extract_class_definition(self, content: str, class_name: str) -> str:
        """Extract class definition from file content."""
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef) and node.name == class_name:
                    lines = content.split("\n")
                    start_line = node.lineno - 1

                    # Find class signature and methods (first 30 lines max)
                    end_line = min(len(lines), start_line + 30)

                    # Try to find the next class/function at the same level
                    for other_node in ast.walk(tree):
                        if (
                            isinstance(other_node, (ast.FunctionDef, ast.ClassDef))
                            and other_node.lineno > node.lineno
                            and other_node.col_offset == node.col_offset
                        ):
                            end_line = min(end_line, other_node.lineno - 1)

                    return "\n".join(lines[start_line:end_line])

            return ""
        except SyntaxError:
            # Fallback to regex if AST parsing fails
            pattern = rf"class\s+{re.escape(class_name)}\s*[(\:]"
            lines = content.split("\n")
            for i, line in enumerate(lines):
                if re.search(pattern, line):
                    # Return the class signature and first few lines
                    end_idx = min(len(lines), i + 15)
                    return "\n".join(lines[i:end_idx])
            return ""
