"""Agentic code reviewer with iterative context gathering capabilities."""

import json
import logging
from typing import Any, Dict, List, Optional

from .ai_providers.base import AIProvider
from .context_tool import ContextTool
from .function_schemas import get_context_tool_schemas, get_review_analysis_schema
from .models import ChangeType, FileDiff, ReviewAnalysis, ReviewComment, ReviewIssue, ReviewSeverity
from .prompt_manager import PromptManager

logger = logging.getLogger(__name__)


class AgenticReviewer:
    """
    Agentic code reviewer that can iteratively gather context and make informed decisions.

    The reviewer works in an iterative loop:
    1. Analyze the initial diff/hunk
    2. Decide if additional context is needed
    3. Use context tools to gather more information
    4. Repeat until sufficient context or max iterations
    5. Generate final comprehensive review
    """

    def __init__(
        self,
        ai_provider: AIProvider,
        context_tool: ContextTool,
        max_iterations: int = 5,
        max_context_calls_per_iteration: int = 3,
    ):
        """
        Initialize the agentic reviewer.

        Args:
            ai_provider: AI provider instance for generating responses
            context_tool: Context tool for gathering additional information
            max_iterations: Maximum number of context-gathering iterations
            max_context_calls_per_iteration: Max context tool calls per iteration
        """
        self.ai_provider = ai_provider
        self.context_tool = context_tool
        self.max_iterations = max_iterations
        self.max_context_calls_per_iteration = max_context_calls_per_iteration
        self.prompt_manager = PromptManager()
        self.system_prompt = self.prompt_manager.get_agentic_system_prompt()

    async def analyze_file(self, file_diff: FileDiff) -> ReviewAnalysis:
        """
        Analyze a file with iterative context gathering.

        Args:
            file_diff: The file diff to analyze

        Returns:
            ReviewAnalysis with comprehensive context-aware feedback
        """
        logger.info(f"Starting agentic analysis of {file_diff.filename}")

        # Prepare initial context
        context_history = []
        iteration = 0

        # Create initial analysis prompt
        initial_prompt = self._create_initial_analysis_prompt(file_diff)
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": initial_prompt},
        ]

        # Iterative context gathering loop
        while iteration < self.max_iterations:
            iteration += 1
            logger.debug(f"Agentic analysis iteration {iteration} for {file_diff.filename}")

            # Get available functions (context tools + final analysis)
            available_functions = get_context_tool_schemas()
            if iteration > 1:  # Allow final analysis after first iteration
                available_functions.append(get_review_analysis_schema())

            # Generate AI response
            try:
                response = await self.ai_provider.generate_response(
                    messages=messages,
                    functions=available_functions,
                    function_choice="auto",
                )

                if not response.function_calls:
                    # No function calls - AI might be providing direct feedback
                    if response.content:
                        messages.append({"role": "assistant", "content": response.content})
                        # Encourage the AI to use tools or provide final analysis
                        messages.append(
                            {
                                "role": "user",
                                "content": (
                                    "Please either gather more context using the available tools, "
                                    "or provide your final review analysis using create_review_analysis."
                                ),
                            }
                        )
                    continue

                # Process function calls
                final_analysis = None
                context_calls_this_iteration = 0

                for func_call in response.function_calls:
                    if func_call.name == "create_review_analysis":
                        # Final analysis provided
                        final_analysis = func_call.arguments
                        break

                    if context_calls_this_iteration >= self.max_context_calls_per_iteration:
                        logger.warning(
                            f"Max context calls ({self.max_context_calls_per_iteration}) "
                            f"reached in iteration {iteration}"
                        )
                        break

                    # Execute context tool call
                    context_result = await self._execute_context_call(func_call)
                    context_history.append(
                        {
                            "tool": func_call.name,
                            "args": func_call.arguments,
                            "result": context_result,
                        }
                    )

                    # Add the function call and result to conversation
                    messages.append(
                        {
                            "role": "assistant",
                            "content": f"I'm calling {func_call.name} with "
                            f"arguments: {json.dumps(func_call.arguments)}",
                        }
                    )
                    messages.append(
                        {
                            "role": "user",
                            "content": f"Result: {json.dumps(context_result)}",
                        }
                    )

                    context_calls_this_iteration += 1

                if final_analysis:
                    # AI provided final analysis
                    return self._create_review_analysis_from_response(
                        final_analysis, file_diff, context_history
                    )

                # Continue to next iteration if no final analysis
                if context_calls_this_iteration == 0:
                    # AI didn't make any useful calls, prompt for decision
                    messages.append(
                        {
                            "role": "user",
                            "content": (
                                "Please either gather more specific context using the available tools, "
                                "or if you have enough information, provide your final review using "
                                "create_review_analysis."
                            ),
                        }
                    )

            except Exception as e:
                logger.error(f"Error in agentic analysis iteration {iteration}: {e}")
                break

        # Max iterations reached without final analysis - create fallback
        logger.warning(
            f"Max iterations ({self.max_iterations}) reached for {file_diff.filename}, "
            "creating fallback analysis"
        )
        return self._create_fallback_analysis(file_diff, context_history)

    async def _execute_context_call(self, func_call) -> Dict[str, Any]:
        """Execute a context tool function call."""
        try:
            if func_call.name == "get_file_content":
                return self.context_tool.get_file_content(**func_call.arguments)
            elif func_call.name == "search_codebase":
                return self.context_tool.search_codebase(**func_call.arguments)
            elif func_call.name == "find_function_definition":
                return self.context_tool.find_function_definition(**func_call.arguments)
            elif func_call.name == "find_class_definition":
                return self.context_tool.find_class_definition(**func_call.arguments)
            elif func_call.name == "find_import_usages":
                return self.context_tool.find_import_usages(**func_call.arguments)
            elif func_call.name == "find_test_files":
                return self.context_tool.find_test_files(**func_call.arguments)
            else:
                return {
                    "success": False,
                    "error": f"Unknown function: {func_call.name}",
                }
        except Exception as e:
            logger.error(f"Error executing context call {func_call.name}: {e}")
            return {"success": False, "error": str(e)}

    def _create_initial_analysis_prompt(self, file_diff: FileDiff) -> str:
        """Create the initial analysis prompt for a file diff."""
        # Create a summary of the changes
        hunks_summary = []
        for i, hunk in enumerate(file_diff.hunks):
            hunk_lines = []
            for line in hunk.lines:
                if line.type.value == "+":
                    hunk_lines.append(f"+{line.new_line_number:4d}: {line.content}")
                elif line.type.value == "-":
                    hunk_lines.append(f"-{line.old_line_number:4d}: {line.content}")
                else:
                    hunk_lines.append(f" {line.new_line_number:4d}: {line.content}")

            hunks_summary.append(f"Hunk {i+1}:\n{hunk.header}\n" + "\n".join(hunk_lines))

        prompt = f"""Please analyze the following code changes in file: {file_diff.filename}

File Status: {file_diff.status}
Additions: +{file_diff.additions}
Deletions: -{file_diff.deletions}

Changes:
{'=' * 80}
{chr(10).join(hunks_summary)}
{'=' * 80}

Please analyze these changes and decide if you need additional context to
provide a thorough review. Consider:

1. Do these changes affect public APIs or interfaces?
2. Are there function/class definitions that I should examine?
3. Are there imports or dependencies that might be impacted?
4. Are there related test files I should check?
5. Do I need to understand how these changes integrate with the broader codebase?

You can use the available context tools to gather more information, or if you have
sufficient context from the diff alone, provide your final analysis using
    create_review_analysis."""

        return prompt

    def _create_review_analysis_from_response(
        self,
        analysis_data: Dict[str, Any],
        file_diff: FileDiff,
        context_history: List[Dict[str, Any]],
    ) -> ReviewAnalysis:
        """Create ReviewAnalysis from AI response data."""
        try:
            # Convert issues from AI response to ReviewIssue objects
            issues = []
            comments = []

            for issue_data in analysis_data.get("issues", []):
                try:
                    severity = ReviewSeverity(issue_data["severity"])
                    change_type = ChangeType(issue_data["change_type"])
                    target_lines = issue_data.get("target_lines", [])

                    if not target_lines:
                        logger.warning(f"Issue '{issue_data.get('title')}' has no target_lines, skipping")
                        continue

                    # Create the issue
                    first_line = min(target_lines)
                    last_line = max(target_lines)

                    issue = ReviewIssue(
                        title=issue_data["title"],
                        description=issue_data["description"],
                        severity=severity,
                        file_path=file_diff.filename,
                        start_line=first_line if first_line != last_line else None,
                        line=last_line,
                        suggestion=issue_data.get("suggestion"),
                        change_type=change_type,
                    )

                    # Store the AI-determined side for comment creation
                    issue._ai_side = issue_data.get("side", "RIGHT")
                    issues.append(issue)

                    # Create corresponding comment
                    comment = self._create_comment_from_issue(issue, file_diff)
                    if comment:
                        comments.append(comment)

                except Exception as e:
                    logger.error(f"Error processing issue: {e}")
                    continue

            # Create overall comment with context summary
            overall_comment = analysis_data.get("overall_assessment", f"Review for {file_diff.filename}")
            context_summary = analysis_data.get("context_summary", "")

            if context_summary:
                overall_comment += f"\n\n**Context Analysis:** {context_summary}"

            return ReviewAnalysis(
                overall_comment=overall_comment,
                issues=issues,
                comments=comments,
                file_path=file_diff.filename,
                confidence=0.95,  # High confidence due to context gathering
            )

        except Exception as e:
            logger.error(f"Error creating review analysis from response: {e}")
            return self._create_fallback_analysis(file_diff, context_history)

    def _create_comment_from_issue(
        self, issue: ReviewIssue, file_diff: FileDiff
    ) -> Optional[ReviewComment]:
        """Create a ReviewComment from a ReviewIssue."""
        try:
            # Build comment body
            badge = self._severity_badge_markdown(issue.severity)
            comment_body = f"{badge}\n\n**{issue.title}**\n\n{issue.description}"

            if issue.suggestion:
                comment_body += f"\n\n```suggestion\n{issue.suggestion}\n```"

            # Use AI-determined side, with RIGHT as fallback
            side = getattr(issue, "_ai_side", "RIGHT")
            start_side = side if issue.start_line is not None else None

            return ReviewComment(
                body=comment_body,
                path=file_diff.filename,
                line=issue.line,
                start_line=issue.start_line,
                side=side,
                start_side=start_side,
                severity=issue.severity,
            )

        except Exception as e:
            logger.error(f"Error creating comment from issue: {e}")
            return None

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

    def _create_fallback_analysis(
        self, file_diff: FileDiff, context_history: List[Dict[str, Any]]
    ) -> ReviewAnalysis:
        """Create a fallback analysis when the agentic process doesn't complete normally."""
        context_summary = (
            f"Gathered context from {len(context_history)} tool calls"
            if context_history
            else "Limited context analysis"
        )

        return ReviewAnalysis(
            overall_comment=f"Automated review of {file_diff.filename}. {context_summary}",
            issues=[],
            comments=[],
            file_path=file_diff.filename,
            confidence=0.5,  # Lower confidence for fallback
        )
