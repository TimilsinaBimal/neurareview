"""Data models for NeuraReview."""

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional


class ReviewSeverity(Enum):
    """Severity levels for review comments."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class ChangeType(Enum):
    """Types of changes for review comments - focused on critical issues only."""

    BUG = "bug"
    PERFORMANCE = "performance"
    SECURITY = "security"
    MEMORY = "memory"
    ERROR_HANDLING = "error_handling"


class LineType(Enum):
    """Types of lines in a diff."""

    ADDED = "+"
    REMOVED = "-"
    CONTEXT = " "


@dataclass
class DiffLine:
    """Represents a single line in a diff."""

    type: LineType
    content: str
    old_line_number: Optional[int]
    new_line_number: Optional[int]


@dataclass
class DiffHunk:
    """Represents a hunk in a diff."""

    old_start: int
    old_count: int
    new_start: int
    new_count: int
    lines: List[DiffLine]
    header: str


@dataclass
class FileDiff:
    """Represents changes to a single file."""

    filename: str
    old_filename: Optional[str]
    status: str  # added, modified, removed, renamed
    hunks: List[DiffHunk]
    patch: str
    additions: int
    deletions: int


@dataclass
class ReviewComment:
    """Represents a review comment to be posted."""

    body: str
    path: str
    line: Optional[int] = None
    start_line: Optional[int] = None
    side: Optional[str] = None
    start_side: Optional[str] = None
    severity: ReviewSeverity = ReviewSeverity.MEDIUM


@dataclass
class ReviewIssue:
    """Represents an issue found during code review."""

    title: str
    description: str
    severity: ReviewSeverity
    file_path: str
    line: Optional[int]  # End line of the comment
    start_line: Optional[int]  # Start line of the comment
    suggestion: Optional[str] = None
    category: str = "general"
    change_type: ChangeType = ChangeType.OTHER


@dataclass
class ReviewAnalysis:
    """Complete analysis result for a file or PR."""

    overall_comment: str
    issues: List[ReviewIssue]
    comments: List[ReviewComment]
    file_path: str
    confidence: float = 1.0


@dataclass
class PRData:
    """Pull request data."""

    number: int
    title: str
    description: str
    head_sha: str
    base_sha: str
    files: List[FileDiff]
    repository: str
