"""Comment management and formatting for GitHub reviews."""

import logging
from typing import List, Dict, Any

from .models import (
    ReviewAnalysis,
    ReviewComment,
    ReviewSeverity,
    ChangeType,
    ReviewIssue,
)


logger = logging.getLogger(__name__)


class CommentManager:
    """Manages review comment formatting and organization."""

    def __init__(self):
        """Initialize comment manager."""
        # Simplified badge system - just use emojis for better performance
        self.severity_emojis = {
            ReviewSeverity.CRITICAL: "🔴",
            ReviewSeverity.HIGH: "🟠",
            ReviewSeverity.MEDIUM: "🟡",
            ReviewSeverity.LOW: "🔵",
            ReviewSeverity.INFO: "ℹ️",
        }
        self.changetype_emojis = {
            ChangeType.BUG: "🐛",
            ChangeType.SECURITY: "🔒",
            ChangeType.PERFORMANCE: "⚡",
            ChangeType.REFACTOR: "♻️",
            ChangeType.STYLE: "🎨",
            ChangeType.DOCUMENTATION: "📝",
            ChangeType.TEST: "🧪",
            ChangeType.OTHER: "🔧",
        }

    def _get_badges(self, severity: ReviewSeverity, change_type: ChangeType) -> str:
        """Get emoji badges for severity and change type."""
        severity_emoji = self.severity_emojis.get(severity, "")
        changetype_emoji = self.changetype_emojis.get(change_type, "")
        return f"{severity_emoji} {changetype_emoji}".strip()

    def format_overall_review(self, analyses: List[ReviewAnalysis]) -> str:
        """Format overall review comment from multiple file analyses."""
        if not analyses:
            return "No files were analyzed in this review."

        # Count issues by severity
        severity_counts = {severity: 0 for severity in ReviewSeverity}
        total_files = len(analyses)
        files_with_issues = 0

        for analysis in analyses:
            if analysis.issues:
                files_with_issues += 1
                for issue in analysis.issues:
                    severity_counts[issue.severity] += 1

        # Create summary
        summary_parts = []

        # Header
        summary_parts.append("## 🤖 AI Code Review Summary")
        summary_parts.append(f"*Reviewed {total_files} files*")
        summary_parts.append("")

        # Issue summary
        if any(count > 0 for count in severity_counts.values()):
            summary_parts.append("### Issues Found")

            if severity_counts[ReviewSeverity.CRITICAL] > 0:
                summary_parts.append(
                    f"🔴 **{severity_counts[ReviewSeverity.CRITICAL]} Critical** - "
                    "Requires immediate attention"
                )
            if severity_counts[ReviewSeverity.HIGH] > 0:
                summary_parts.append(
                    f"🟠 **{severity_counts[ReviewSeverity.HIGH]} High** - "
                    "Should be addressed"
                )
            if severity_counts[ReviewSeverity.MEDIUM] > 0:
                summary_parts.append(
                    f"🟡 **{severity_counts[ReviewSeverity.MEDIUM]} Medium** - "
                    "Consider addressing"
                )
            if severity_counts[ReviewSeverity.LOW] > 0:
                summary_parts.append(
                    f"🔵 **{severity_counts[ReviewSeverity.LOW]} Low** - "
                    "Minor improvements"
                )
            if severity_counts[ReviewSeverity.INFO] > 0:
                summary_parts.append(
                    f"ℹ️ **{severity_counts[ReviewSeverity.INFO]} Info** - "
                    "Educational notes"
                )

            summary_parts.append("")

        else:
            summary_parts.append("### ✅ No Issues Found")
            summary_parts.append("Great job! The code changes look good.")
            summary_parts.append("")

        # File-by-file summary
        if files_with_issues > 0:
            summary_parts.append("### Files Reviewed")
            for analysis in analyses:
                if analysis.issues:
                    issue_count = len(analysis.issues)
                    critical_count = sum(
                        1
                        for issue in analysis.issues
                        if issue.severity == ReviewSeverity.CRITICAL
                    )
                    high_count = sum(
                        1
                        for issue in analysis.issues
                        if issue.severity == ReviewSeverity.HIGH
                    )

                    status_icon = (
                        "🔴" if critical_count > 0 else "🟠" if high_count > 0 else "🟡"
                    )
                    summary_parts.append(
                        f"{status_icon} `{analysis.file_path}` - {issue_count} issues"
                    )
                else:
                    summary_parts.append(f"✅ `{analysis.file_path}` - No issues")

            summary_parts.append("")

        # Footer
        summary_parts.append("---")
        summary_parts.append("*This review was generated by NeuraReview AI*")

        return "\n".join(summary_parts)

    def format_review_comment(
        self,
        issue: ReviewIssue,
    ) -> str:
        """Formats a single review comment with badges and suggestion."""
        badges = self._get_badges(issue.severity, issue.change_type)
        type_label = issue.change_type.value.capitalize()
        body = (
            f"{badges}  `Type: {type_label}`\n\n"
            f"**{issue.title}**\n\n{issue.description}"
        )

        if issue.suggestion:
            suggestion = self._clean_suggestion(issue.suggestion)
            if suggestion:
                body += f"\n\n```suggestion\n{suggestion}\n```"

        return body

    def _clean_suggestion(self, suggestion: str) -> str:
        """Cleans up the suggestion string."""
        if not suggestion:
            return ""
        return suggestion.strip().removeprefix("```").removesuffix("```").strip()

    def group_comments_by_severity(
        self, comments: List[ReviewComment]
    ) -> Dict[ReviewSeverity, List[ReviewComment]]:
        """Group comments by severity level."""
        grouped = {severity: [] for severity in ReviewSeverity}

        for comment in comments:
            grouped[comment.severity].append(comment)

        return grouped

    def filter_comments_by_confidence(
        self, analyses: List[ReviewAnalysis], min_confidence: float = 0.7
    ) -> List[ReviewComment]:
        """Filter comments based on confidence threshold."""
        filtered_comments = []

        for analysis in analyses:
            if analysis.confidence >= min_confidence:
                filtered_comments.extend(analysis.comments)
            else:
                logger.info(
                    f"Filtered out low-confidence analysis for {analysis.file_path} "
                    f"(confidence: {analysis.confidence})"
                )

        return filtered_comments

    def deduplicate_comments(
        self, comments: List[ReviewComment]
    ) -> List[ReviewComment]:
        """Remove duplicate comments based on content and position."""
        seen = set()
        deduplicated = []

        for comment in comments:
            # Create a key based on file path, line, and content hash
            key = (comment.path, comment.line, hash(comment.body))

            if key not in seen:
                seen.add(key)
                deduplicated.append(comment)

        return deduplicated

    def limit_comments_per_file(
        self, comments: List[ReviewComment], max_per_file: int = 10
    ) -> List[ReviewComment]:
        """Limit the number of comments per file to avoid spam."""
        file_counts = {}
        limited_comments = []

        # Sort by severity (critical first)
        severity_order = {
            ReviewSeverity.CRITICAL: 0,
            ReviewSeverity.HIGH: 1,
            ReviewSeverity.MEDIUM: 2,
            ReviewSeverity.LOW: 3,
            ReviewSeverity.INFO: 4,
        }

        sorted_comments = sorted(
            comments, key=lambda c: severity_order.get(c.severity, 5)
        )

        for comment in sorted_comments:
            file_path = comment.path
            current_count = file_counts.get(file_path, 0)

            if current_count < max_per_file:
                limited_comments.append(comment)
                file_counts[file_path] = current_count + 1
            else:
                logger.debug(f"Skipped comment for {file_path} (limit reached)")

        return limited_comments

    def prepare_review_data(
        self,
        analyses: List[ReviewAnalysis],
        max_comments_per_file: int = 10,
        min_confidence: float = 0.7,
    ) -> Dict[str, Any]:
        """Prepare final review data for posting to GitHub."""
        # Filter and process comments
        all_comments = []
        for analysis in analyses:
            all_comments.extend(analysis.comments)

        # Apply filters
        filtered_comments = self.filter_comments_by_confidence(analyses, min_confidence)
        deduplicated_comments = self.deduplicate_comments(filtered_comments)
        limited_comments = self.limit_comments_per_file(
            deduplicated_comments, max_comments_per_file
        )

        # Generate overall review
        overall_comment = self.format_overall_review(analyses)

        # Log statistics
        logger.info(
            f"Review prepared: {len(limited_comments)} comments from "
            f"{len(analyses)} files"
        )
        logger.info(
            f"Filtered: {len(all_comments)} -> {len(filtered_comments)} -> "
            f"{len(deduplicated_comments)} -> {len(limited_comments)}"
        )

        return {
            "overall_comment": overall_comment,
            "comments": limited_comments,
            "statistics": {
                "total_files": len(analyses),
                "files_with_issues": len([a for a in analyses if a.issues]),
                "total_issues": sum(len(a.issues) for a in analyses),
                "total_comments": len(limited_comments),
            },
        }
