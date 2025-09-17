"""GitHub API client for NeuraReview."""

import logging
from typing import List

from github import Auth, Github
from github.GithubException import GithubException
from github.PullRequest import PullRequest
from github.Repository import Repository

from .config import GitHubConfig
from .models import FileDiff, PRData, ReviewComment

logger = logging.getLogger(__name__)


class GitHubClient:
    """GitHub API client with proper error handling."""

    def __init__(self, config: GitHubConfig):
        """Initialize GitHub client."""
        self.config = config
        auth = Auth.Token(config.token)
        self.github = Github(auth=auth)

    def get_repository(self, repo_name: str) -> Repository:
        """Get repository by name (owner/repo)."""
        try:
            return self.github.get_repo(repo_name)
        except GithubException as e:
            logger.error(f"Failed to get repository {repo_name}: {e}")
            raise

    def get_pull_request(self, repo_name: str, pr_number: int) -> PullRequest:
        """Get pull request by number."""
        try:
            repo = self.get_repository(repo_name)
            return repo.get_pull(pr_number)
        except GithubException as e:
            logger.error(f"Failed to get PR #{pr_number} from {repo_name}: {e}")
            raise

    def fetch_pr_data(self, repo_name: str, pr_number: int) -> PRData:
        """Fetch complete PR data including files and diffs."""
        try:
            pr = self.get_pull_request(repo_name, pr_number)

            # Get all files in the PR
            files = []
            for github_file in pr.get_files():
                file_diff = FileDiff(
                    filename=github_file.filename,
                    old_filename=getattr(github_file, "previous_filename", None),
                    status=github_file.status,
                    hunks=[],  # Will be populated by diff parser
                    patch=github_file.patch or "",
                    additions=github_file.additions,
                    deletions=github_file.deletions,
                )
                files.append(file_diff)

            return PRData(
                number=pr.number,
                title=pr.title,
                description=pr.body or "",
                head_sha=pr.head.sha,
                base_sha=pr.base.sha,
                files=files,
                repository=repo_name,
            )

        except GithubException as e:
            logger.error(f"Failed to fetch PR data: {e}")
            raise

    def post_review(
        self,
        repo_name: str,
        pr_number: int,
        overall_comment: str,
        comments: List[ReviewComment],
    ) -> bool:
        """Post a review with comments to the PR."""
        try:
            pr = self.get_pull_request(repo_name, pr_number)

            github_comments = []
            for comment in comments:
                if comment.line is None:
                    logger.warning(
                        f"Skipping comment for {comment.path} "
                        f"due to missing line number"
                    )
                    continue

                github_comment = {
                    "body": comment.body,
                    "path": comment.path,
                    "line": comment.line,
                    "side": comment.side or "RIGHT",
                }

                if comment.start_line is not None:
                    github_comment["start_line"] = comment.start_line
                    github_comment["start_side"] = comment.start_side or "RIGHT"

                github_comments.append(github_comment)

            if not github_comments:
                logger.info("No valid comments to post.")
                if overall_comment:
                    pr.create_issue_comment(overall_comment)
                    logger.info("Posted overall comment as a standalone issue comment.")
                return True

            logger.debug(f"GitHub comments to post: {github_comments}")
            logger.debug(f"comment: {comments}")

            review = pr.create_review(
                body=overall_comment, event="COMMENT", comments=github_comments
            )

            logger.info(f"Successfully posted review #{review.id} to PR #{pr_number}")
            return True

        except GithubException as e:
            logger.error(f"Failed to post review: {e}")
            if hasattr(e, "data") and e.data:
                logger.error(f"GitHub API error details: {e.data}")
            return False

    def post_single_comment(
        self, repo_name: str, pr_number: int, comment: ReviewComment
    ) -> bool:
        """Post a single review comment."""
        try:
            pr = self.get_pull_request(repo_name, pr_number)

            if comment.line is None:
                logger.error("Cannot post comment without a line number.")
                return False

            pr.create_review_comment(
                body=comment.body,
                commit=pr.head,
                path=comment.path,
                line=comment.line,
                side=comment.side or "RIGHT",
            )
            logger.info(f"Successfully posted single comment to {comment.path}")
            return True

        except GithubException as e:
            logger.error(f"Failed to post single comment: {e}")
            return False

    def validate_connection(self) -> bool:
        """Validate GitHub connection and permissions."""
        try:
            # Try to access the GitHub API rate limit instead of user info
            # This requires minimal permissions and validates the token
            rate_limit = self.github.get_rate_limit()
            logger.info(
                f"GitHub API rate limit: "
                f"{rate_limit.core.remaining}/{rate_limit.core.limit}"
            )
            return True
        except GithubException as e:
            logger.error(f"GitHub connection failed: {e}")
            return False
