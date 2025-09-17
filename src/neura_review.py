"""Main NeuraReview application orchestrator."""

import asyncio
import logging
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Optional

from .ai_reviewer import AIReviewer
from .comment_manager import CommentManager
from .config import Config
from .diff_parser import DiffParser
from .github_client import GitHubClient
from .models import FileDiff, ReviewAnalysis

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("neura_review.log"),
    ],
)

logger = logging.getLogger(__name__)


class NeuraReview:
    """Main application class for AI code review."""

    def __init__(self, config: Config):
        """Initialize NeuraReview with configuration."""
        self.config = config
        self.github_client = GitHubClient(config.github)
        self.diff_parser = DiffParser()
        self.ai_reviewer = AIReviewer(config.ai)
        self.comment_manager = CommentManager()

    def review_pull_request(
        self, repo_name: str, pr_number: int, dry_run: bool = False
    ) -> bool:
        """Review a pull request and post comments."""
        try:
            logger.info(f"Starting review of PR #{pr_number} in {repo_name}")

            # Validate GitHub connection
            if not self.github_client.validate_connection():
                logger.error("GitHub connection validation failed")
                return False

            # Fetch PR data
            logger.info("Fetching PR data...")
            pr_data = self.github_client.fetch_pr_data(repo_name, pr_number)

            if not pr_data.files:
                logger.info("No files found in PR")
                return True

            logger.info(f"Found {len(pr_data.files)} files to review")

            # Filter files for review
            reviewable_files = self._filter_reviewable_files(pr_data.files)
            logger.info(
                f"Reviewing {len(reviewable_files)} files "
                f"(skipped {len(pr_data.files) - len(reviewable_files)})"
            )

            if not reviewable_files:
                logger.info("No reviewable files found")
                return True

            # Analyze files
            logger.info("Starting AI analysis...")
            analyses = asyncio.run(self._analyze_files_async(reviewable_files))

            if not analyses:
                logger.warning("No analyses generated")
                return False

            # Prepare review data - focused on critical issues only
            logger.info("Preparing review comments (critical issues only)...")
            review_data = self.comment_manager.prepare_review_data(
                analyses,
                max_comments_per_file=5,  # Reduced for focused reviews
                min_confidence=0.8,  # Higher confidence threshold
            )

            # Log review statistics
            stats = review_data["statistics"]
            logger.info(
                f"Review stats: {stats['total_files']} files, "
                f"{stats['files_with_issues']} with issues, "
                f"{stats['total_issues']} total issues, "
                f"{stats['total_comments']} comments"
            )

            if dry_run:
                logger.info("DRY RUN - Review prepared but not posted")
                self._log_review_preview(review_data)
                return True

            # Post review to GitHub
            logger.info("Posting review to GitHub...")
            success = self.github_client.post_review(
                repo_name=repo_name,
                pr_number=pr_number,
                overall_comment=review_data["overall_comment"],
                comments=review_data["comments"],
            )

            if success:
                logger.info(
                    "Successfully posted review with "
                    f"{len(review_data['comments'])} comments"
                )
            else:
                logger.error("Failed to post review")

            return success

        except Exception as e:
            logger.error(f"Error during PR review: {e}", exc_info=True)
            return False

    def _filter_reviewable_files(self, files: List[FileDiff]) -> List[FileDiff]:
        """Filter files that should be reviewed."""
        reviewable = []

        for file_diff in files:
            # Skip files that don't need review
            if self._should_skip_file(file_diff):
                continue

            # Parse the diff to populate hunks and line maps
            self.diff_parser.parse_file_diff(file_diff)

            # Skip files with no meaningful changes
            if not file_diff.patch or not file_diff.hunks:
                logger.debug(f"Skipping {file_diff.filename} (no meaningful changes)")
                continue

            reviewable.append(file_diff)

        return reviewable

    def _should_skip_file(self, file_diff: FileDiff) -> bool:
        """Determine if a file should be skipped from review."""
        # Skip by file extension
        if any(
            file_diff.filename.lower().endswith(ext)
            for ext in self.config.review.skip_file_types
        ):
            logger.debug(f"Skipping {file_diff.filename} (file type excluded)")
            return True

        # Skip deleted files - no point reviewing deleted code
        if file_diff.status == "removed":
            logger.debug(f"Skipping {file_diff.filename} (file deleted)")
            return True

        # Skip renamed files with no content changes
        if (
            file_diff.status == "renamed"
            and file_diff.additions == 0
            and file_diff.deletions == 0
        ):
            logger.debug(f"Skipping {file_diff.filename} (renamed without changes)")
            return True

        # Skip very large files to avoid overwhelming reviews
        if file_diff.additions + file_diff.deletions > 1000:
            logger.debug(
                f"Skipping {file_diff.filename} (too many changes: "
                f"+{file_diff.additions} -{file_diff.deletions})"
            )
            return True

        return False

    def _analyze_files(self, files: List[FileDiff]) -> List[ReviewAnalysis]:
        """Analyze multiple files in parallel."""
        analyses = []
        # Optimize worker count based on file count and system resources
        max_workers = min(len(files), 5)  # Cap at 5 to avoid API rate limits
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_file = {
                executor.submit(self.ai_reviewer.analyze_file, file_diff): file_diff
                for file_diff in files
            }

            for future in as_completed(future_to_file):
                file_diff = future_to_file[future]
                try:
                    analysis = future.result()
                    # Only include analyses with issues
                    if analysis and analysis.issues:
                        analyses.append(analysis)
                        logger.info(
                            f"Found {len(analysis.issues)} issues in "
                            f"{file_diff.filename}"
                        )
                    else:
                        logger.debug(f"No issues found in {file_diff.filename}")
                except Exception as e:
                    logger.error(f"Failed to analyze {file_diff.filename}: {e}")

        return analyses

    async def _analyze_files_async(self, files: List[FileDiff]) -> List[ReviewAnalysis]:
        """Analyze files concurrently using asyncio and per-hunk parallelism."""
        analyses: List[ReviewAnalysis] = []

        async def analyze_one(file_diff: FileDiff) -> None:
            try:
                # Ensure hunks are parsed
                self.diff_parser.parse_file_diff(file_diff)

                # Analyze hunks in parallel
                tasks = [
                    self.ai_reviewer._analyze_hunk_async(file_diff, hunk)
                    for hunk in file_diff.hunks
                ]
                if not tasks:
                    logger.debug(f"No hunks found in {file_diff.filename}")
                    return

                results = await asyncio.gather(*tasks, return_exceptions=True)

                all_issues = []
                all_comments = []
                for result in results:
                    if isinstance(result, Exception):
                        logger.error(
                            f"Hunk analysis failed for {file_diff.filename}: {result}"
                        )
                        continue
                    issues, comments = result
                    all_issues.extend(issues)
                    all_comments.extend(comments)

                analysis = ReviewAnalysis(
                    overall_comment=f"Review for {file_diff.filename}",
                    issues=all_issues,
                    comments=all_comments,
                    file_path=file_diff.filename,
                    confidence=0.9 if all_issues else 1.0,
                )

                if analysis.issues:
                    analyses.append(analysis)
                    logger.info(
                        f"Found {len(analysis.issues)} issues in {file_diff.filename}"
                    )
                else:
                    logger.debug(f"No issues found in {file_diff.filename}")
            except Exception as e:
                logger.error(f"Failed to analyze {file_diff.filename}: {e}")

        # Limit total concurrency to avoid rate limits
        semaphore = asyncio.Semaphore(5)

        async def sem_task(fd: FileDiff):
            async with semaphore:
                await analyze_one(fd)

        await asyncio.gather(*(sem_task(f) for f in files))
        return analyses

    def _log_review_preview(self, review_data):
        """Log a preview of the review for dry runs."""
        logger.info("=== REVIEW PREVIEW ===")
        logger.info("Overall Comment:")
        logger.info(review_data["overall_comment"])
        logger.info("")

        for i, comment in enumerate(review_data["comments"], 1):
            line_info = (
                f"{comment.line}"
                if comment.start_line is None
                else f"{comment.start_line}-{comment.line}"
            )
            logger.info(f"Comment {i}: {comment.path}:{line_info} ({comment.side})")
            logger.info(f"Severity: {comment.severity.value}")
            logger.info(f"Body: {comment.body[:100]}...")
            logger.info("---")

    def analyze_single_file(
        self, repo_name: str, pr_number: int, filename: str
    ) -> Optional[ReviewAnalysis]:
        """Analyze a single file in a PR."""
        try:
            pr_data = self.github_client.fetch_pr_data(repo_name, pr_number)

            # Find the specific file
            target_file = None
            for file_diff in pr_data.files:
                if file_diff.filename == filename:
                    target_file = file_diff
                    break

            if not target_file:
                logger.error(f"File {filename} not found in PR #{pr_number}")
                return None

            logger.info(f"Analyzing single file: {filename}")
            return self.ai_reviewer.analyze_file(target_file)

        except Exception as e:
            logger.error(f"Error analyzing single file {filename}: {e}")
            return None
