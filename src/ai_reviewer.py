"""AI-powered code reviewer with improved prompts."""

import json
import logging
from typing import Any, Dict

from openai import AsyncOpenAI, OpenAI

from .config import AIConfig
from .diff_parser import DiffParser
from .models import (
    ChangeType,
    DiffHunk,
    FileDiff,
    LineType,
    ReviewAnalysis,
    ReviewComment,
    ReviewIssue,
    ReviewSeverity,
)
from .prompt_manager import PromptManager

logger = logging.getLogger(__name__)


class AIReviewer:
    """AI-powered code reviewer."""

    def __init__(self, config: AIConfig):
        """Initialize AI reviewer."""
        self.config = config
        self.client = OpenAI(api_key=config.api_key)
        self.async_client = AsyncOpenAI(api_key=config.api_key)
        self.diff_parser = DiffParser()
        self.prompt_manager = PromptManager()

    def analyze_file(self, file_diff: FileDiff) -> ReviewAnalysis:
        """Analyze a single file and generate review comments."""
        try:
            # File filtering is now handled at the NeuraReview level
            self.diff_parser.parse_file_diff(file_diff)

            overall_comment = f"Review for {file_diff.filename}"
            all_issues = []
            all_comments = []

            for hunk in file_diff.hunks:
                issues, comments = self._analyze_hunk(file_diff, hunk)
                all_issues.extend(issues)
                all_comments.extend(comments)

            return ReviewAnalysis(
                overall_comment=overall_comment,
                issues=all_issues,
                comments=all_comments,
                file_path=file_diff.filename,
                confidence=0.9 if all_issues else 1.0,
            )

        except Exception as e:
            logger.error(f"Error analyzing file {file_diff.filename}: {e}")
            return self._create_empty_analysis(file_diff.filename, f"Error: {e}")

    async def _analyze_hunk_async(self, file_diff: FileDiff, hunk: DiffHunk):
        """Analyze a single hunk of a file asynchronously."""
        try:
            ai_response = await self._generate_ai_analysis_async(file_diff.filename, hunk)
            issues, comments = self._process_ai_response(ai_response, file_diff.filename, hunk)
            return issues, comments
        except Exception as e:
            logger.error(f"Error analyzing hunk for {file_diff.filename}: {e}", exc_info=True)
            return [], []

    def _create_empty_analysis(self, file_path: str, reason: str) -> ReviewAnalysis:
        """Create an empty review analysis."""
        return ReviewAnalysis(
            overall_comment=f"Skipped analysis for {file_path}: {reason}",
            issues=[],
            comments=[],
            file_path=file_path,
            confidence=1.0,
        )

    def _get_file_language(self, filename: str) -> str:
        """Detect programming language from filename."""
        language_map = {
            ".py": "Python",
            ".js": "JavaScript",
            ".ts": "TypeScript",
            ".jsx": "React JSX",
            ".tsx": "React TSX",
            ".java": "Java",
            ".cpp": "C++",
            ".c": "C",
            ".cs": "C#",
            ".php": "PHP",
            ".rb": "Ruby",
            ".go": "Go",
            ".rs": "Rust",
            ".swift": "Swift",
            ".kt": "Kotlin",
            ".scala": "Scala",
            ".sh": "Shell",
            ".bash": "Bash",
            ".zsh": "Zsh",
            ".html": "HTML",
            ".css": "CSS",
            ".scss": "SCSS",
            ".sass": "Sass",
            ".less": "Less",
        }

        for ext, lang in language_map.items():
            if filename.lower().endswith(ext):
                return lang

        return "Unknown"

    async def _generate_ai_analysis_async(self, filename: str, hunk: DiffHunk) -> Dict[str, Any]:
        """Generate AI analysis for a single hunk."""
        language = self._get_file_language(filename)
        system_prompt = self.prompt_manager.get_traditional_review_prompt(language)
        user_prompt = self._create_user_prompt_for_hunk(filename, hunk)

        function_schema = {
            "type": "function",
            "name": "create_review_analysis",
            "description": ("Create a structured code review analysis for a hunk"),
            "strict": True,
            "parameters": {
                "type": "object",
                "properties": {
                    "issues": {
                        "type": "array",
                        "description": ("List of specific issues found in the hunk"),
                        "items": {
                            "type": "object",
                            "properties": {
                                "title": {"type": "string"},
                                "description": {"type": "string"},
                                "severity": {
                                    "type": "string",
                                    "enum": [
                                        "critical",
                                        "high",
                                        "medium",
                                        "low",
                                        "info",
                                    ],
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
                                },
                                "target_lines": {
                                    "type": "array",
                                    "description": (
                                        "Line numbers from the diff that this " "issue applies to"
                                    ),
                                    "items": {"type": "integer"},
                                },
                                "suggestion": {"type": ["string", "null"]},
                            },
                            "required": [
                                "title",
                                "description",
                                "severity",
                                "change_type",
                                "target_lines",
                                "suggestion",
                            ],
                            "additionalProperties": False,
                        },
                    }
                },
                "required": ["issues"],
                "additionalProperties": False,
            },
        }

        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]
            response = await self.async_client.responses.create(
                store=False,
                model="gpt-5-mini",
                input=messages,
                tools=[function_schema],
                tool_choice="auto",
                parallel_tool_calls=False,
                reasoning={"effort": "low", "summary": "auto"},
                max_output_tokens=self.config.max_tokens,
                stream=False,
            )

            arguments: Dict[str, Any] = {}
            for output in response.output:
                logger.debug(f"AI response: {output}")
                if output.type == "function_call":
                    raw_arguments = output.arguments
                    logger.debug(f"Raw AI response arguments: {raw_arguments}")
                    arguments = json.loads(raw_arguments)
                else:
                    logger.warning(output)

            if not arguments:
                logger.warning("No arguments in AI response")
                return {"issues": []}
            return arguments
        except Exception as e:
            logger.error(f"AI analysis failed for hunk in {filename}: {e}")
            return {"issues": []}

    def _create_user_prompt_for_hunk(self, filename: str, hunk: DiffHunk) -> str:
        """Create user prompt with hunk changes."""
        hunk_lines = []
        for line in hunk.lines:
            if line.type.value == "+":
                hunk_lines.append(f"+{line.new_line_number:4d}: {line.content}")
            elif line.type.value == "-":
                hunk_lines.append(f"-{line.old_line_number:4d}: {line.content}")
            else:
                hunk_lines.append(f" {line.new_line_number:4d}: {line.content}")

        hunk_diff = "\n".join(hunk_lines)

        prompt = (
            f"Please review the following code changes in a hunk "
            f"from the file `{filename}`:\n\n"
            f"```diff\n{hunk.header}\n{hunk_diff}\n```\n\n"
            f"**REQUIREMENTS:**\n"
            f"1. Analyze EVERY added and removed line.\n"
            f"2. For each issue, provide the exact line number from the diff above.\n"
            f"3. For suggestions, provide ONLY pure code, no text, no markdown, "
            f"no explanations in the suggestion field."
        )
        return prompt

    def _process_ai_response(
        self, ai_response: Dict[str, Any], filename: str, hunk: DiffHunk
    ) -> tuple[list[ReviewIssue], list[ReviewComment]]:
        """Process AI response into structured review analysis for a hunk."""
        issues = []
        comments = []

        for issue_data in ai_response.get("issues", []):
            try:
                severity = ReviewSeverity(issue_data["severity"])
                change_type = ChangeType(issue_data["change_type"])
                target_lines = issue_data.get("target_lines", [])

                if not target_lines:
                    logger.warning(f"Issue '{issue_data.get('title')}' has no target_lines, " f"skipping")
                    continue

                # Find the actual diff lines for the target line numbers
                diff_lines = self._find_diff_lines_for_targets(hunk, target_lines)

                if not diff_lines:
                    logger.warning(
                        f"Could not find any diff lines for target_lines "
                        f"{target_lines} in issue '{issue_data.get('title')}'"
                    )
                    continue

                # Create the issue with the first and last line numbers
                first_line = min(target_lines)
                last_line = max(target_lines)

                issue = ReviewIssue(
                    title=issue_data["title"],
                    description=issue_data["description"],
                    severity=severity,
                    file_path=filename,
                    start_line=first_line if first_line != last_line else None,
                    line=last_line,
                    suggestion=issue_data.get("suggestion"),
                    change_type=change_type,
                )
                issues.append(issue)

                # Create the review comment using hunk-aware logic
                comment = self._create_comment_from_diff_lines(diff_lines, issue, filename, hunk)

                if comment:
                    comments.append(comment)

            except Exception as e:
                logger.error(f"Error processing AI issue for {filename}: {e}")
                continue

        return issues, comments

    def _find_diff_lines_for_targets(self, hunk: DiffHunk, target_lines: list) -> list:
        """Find DiffLine objects for the given target line numbers."""
        diff_lines = []
        for target_line in target_lines:
            for line in hunk.lines:
                if line.new_line_number == target_line or line.old_line_number == target_line:
                    diff_lines.append(line)
                    break
        return diff_lines

    def _create_comment_from_diff_lines(
        self, diff_lines: list, issue: "ReviewIssue", filename: str, hunk: DiffHunk
    ) -> "ReviewComment":
        """Create a ReviewComment with correct parameters and
        indentation-aware suggestions.

        - Chooses multi-line comment ranges when consecutive lines exist
        - Sets side/start_side appropriately (RIGHT for additions,
          LEFT for removals)
        - Re-indents code suggestions to match the target line indentation
        """
        if not diff_lines:
            return None

        # Helper to compute longest consecutive range
        def longest_consecutive_range(
            numbers: list[int],
        ) -> tuple[int, int] | None:
            if not numbers:
                return None
            numbers = sorted(n for n in numbers if n is not None)
            if not numbers:
                return None
            best_start = cur_start = numbers[0]
            best_end = cur_end = numbers[0]
            for n in numbers[1:]:
                if n == cur_end + 1:
                    cur_end = n
                else:
                    if (cur_end - cur_start) > (best_end - best_start):
                        best_start, best_end = cur_start, cur_end
                    cur_start = cur_end = n
            if (cur_end - cur_start) > (best_end - best_start):
                best_start, best_end = cur_start, cur_end
            return (best_start, best_end)

        # Partition lines by type
        added_lines = [diff_line for diff_line in diff_lines if diff_line.type == LineType.ADDED]
        removed_lines = [diff_line for diff_line in diff_lines if diff_line.type == LineType.REMOVED]

        added_nums = [diff_line.new_line_number for diff_line in added_lines if diff_line.new_line_number]
        removed_nums = [
            diff_line.old_line_number for diff_line in removed_lines if diff_line.old_line_number
        ]

        added_range = longest_consecutive_range(added_nums)
        removed_range = longest_consecutive_range(removed_nums)

        # Choose the best range: prefer added over removed, and longer ranges first
        start_line_number = None
        line_number = None
        side = "RIGHT"
        start_side = None

        def range_length(r: tuple[int, int] | None) -> int:
            if not r:
                return 0
            return r[1] - r[0]

        if added_range and range_length(added_range) >= max(1, range_length(removed_range)):
            start_line_number, line_number = added_range
            side = "RIGHT"
            start_side = "RIGHT"
            # Choose a primary reference line for indentation (the start of the range)
            ref_line = next(
                (dl for dl in added_lines if dl.new_line_number == start_line_number),
                added_lines[0],
            )
        elif removed_range and range_length(removed_range) >= 1:
            start_line_number, line_number = removed_range
            side = "LEFT"
            start_side = "LEFT"
            ref_line = next(
                (dl for dl in removed_lines if dl.old_line_number == start_line_number),
                removed_lines[0],
            )
        else:
            # Fallback to a single primary line: prefer added, then removed, then any
            primary_line = None
            for diff_line in diff_lines:
                if diff_line.type == LineType.ADDED:
                    primary_line = diff_line
                    break
            if not primary_line:
                for diff_line in diff_lines:
                    if diff_line.type == LineType.REMOVED:
                        primary_line = diff_line
                        break
            if not primary_line:
                primary_line = diff_lines[0]

            if primary_line.type == LineType.ADDED:
                side = "RIGHT"
                line_number = primary_line.new_line_number
            elif primary_line.type == LineType.REMOVED:
                side = "LEFT"
                line_number = primary_line.old_line_number
            else:
                side = "RIGHT"
                line_number = primary_line.new_line_number
            ref_line = primary_line

        # Build the comment body with severity badge and suggestion.
        # Reindent suggestion to match target context for languages like Python.
        badge = self._severity_badge_markdown(issue.severity)
        comment_body = f"{badge}\n\n**{issue.title}**\n\n{issue.description}"

        if issue.suggestion:
            raw_suggestion = self._clean_suggestion(issue.suggestion)
            if raw_suggestion:
                base_indent = self._leading_whitespace(ref_line.content or "")
                normalized = self._reindent_suggestion(raw_suggestion, base_indent)
                comment_body += f"\n\n```suggestion\n{normalized}\n```"

        return ReviewComment(
            body=comment_body,
            path=filename,
            line=line_number,
            start_line=start_line_number,
            side=side,
            start_side=start_side if start_line_number is not None else None,
            severity=issue.severity,
        )

    def _leading_whitespace(self, text: str) -> str:
        """Return the exact leading whitespace of a line (tabs/spaces preserved)."""
        i = 0
        while i < len(text) and text[i] in (" ", "\t"):
            i += 1
        return text[:i]

    def _reindent_suggestion(self, suggestion: str, base_indent: str) -> str:
        """Re-indent a multi-line suggestion to align with target indentation.

        Preserves relative indentation inside the suggestion while applying the
        base indentation derived from the target context.
        """
        lines = suggestion.split("\n")
        # Determine minimal indentation among non-empty lines
        non_empty = [ln for ln in lines if ln.strip()]
        if not non_empty:
            return suggestion

        def leading_ws(s: str) -> int:
            j = 0
            while j < len(s) and s[j] in (" ", "\t"):
                j += 1
            return j

        min_indent = min(leading_ws(ln) for ln in non_empty)

        reindented: list[str] = []
        for ln in lines:
            if ln.strip():
                # Strip the common minimal indent, then apply base indent
                without_common = ln[min_indent:] if len(ln) >= min_indent else ln.lstrip()
                reindented.append(f"{base_indent}{without_common}")
            else:
                reindented.append(ln)
        normalized = "\n".join(reindented).rstrip()
        # Enforce drop-in replacement: do not include lines less-indented than base
        base_len = len(base_indent)
        filtered: list[str] = []
        for ln in normalized.split("\n"):
            if ln.strip() and len(self._leading_whitespace(ln)) < base_len:
                continue
            filtered.append(ln)
        return "\n".join(filtered).rstrip()

    def _severity_badge_markdown(self, severity: ReviewSeverity) -> str:
        """Return a shields.io markdown badge for the severity level."""
        color_map = {
            ReviewSeverity.CRITICAL: "red",
            ReviewSeverity.HIGH: "orange",
            ReviewSeverity.MEDIUM: "yellow",
            ReviewSeverity.LOW: "blue",
            ReviewSeverity.INFO: "informational",
        }
        color = color_map.get(severity, "lightgrey")
        label = severity.value.capitalize()
        return f"![Severity: {label}]" f"(https://img.shields.io/badge/Severity-{label}-{color})"

    def _clean_suggestion(self, suggestion: str) -> str:
        """Clean suggestion to ensure it's pure code only."""
        if not suggestion:
            return suggestion

        cleaned = suggestion.strip()

        # Remove markdown code blocks
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            cleaned = "\n".join(lines)

        return cleaned.strip()
