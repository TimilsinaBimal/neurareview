import argparse
import os
import sys

from .config import Config
from .neura_review import NeuraReview


def main() -> int:
    parser = argparse.ArgumentParser(
        description="NeuraReview - AI-powered code review agent",
    )
    parser.add_argument("--repo", required=True, help="owner/repo")
    parser.add_argument("--pr", type=int, required=True, help="PR number")
    parser.add_argument("--dry-run", action="store_true", help="Preview only")
    parser.add_argument("--file", help="Analyze only a specific file in the PR")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logs")

    # GitHub Action specific arguments
    parser.add_argument("--github-token", help="GitHub token (for GitHub Actions)")
    parser.add_argument("--openai-api-key", help="OpenAI API key (for GitHub Actions)")

    args = parser.parse_args()

    # Set up logging
    import logging

    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    logger = logging.getLogger(__name__)

    try:
        # Override environment variables if provided via arguments (for GitHub Actions)
        if args.github_token:
            os.environ["GITHUB_TOKEN"] = args.github_token
        if args.openai_api_key:
            os.environ["OPENAI_API_KEY"] = args.openai_api_key

        # Validate required environment variables
        if not os.getenv("OPENAI_API_KEY"):
            logger.error("OPENAI_API_KEY environment variable is required")
            return 1
        if not os.getenv("GITHUB_TOKEN"):
            logger.error("GITHUB_TOKEN environment variable is required")
            return 1

        config = Config.from_env()
        reviewer = NeuraReview(config)

        logger.info(f"Starting NeuraReview for PR #{args.pr} in {args.repo}")

        if args.file:
            logger.info(f"Analyzing single file: {args.file}")
            analysis = reviewer.analyze_single_file(args.repo, args.pr, args.file)
            if analysis is None:
                logger.error("Failed to analyze file")
                return 1
            print(f"Overall: {analysis.overall_comment}")
            print(f"Issues found: {len(analysis.issues)}")
            return 0

        success = reviewer.review_pull_request(
            repo_name=args.repo, pr_number=args.pr, dry_run=args.dry_run
        )

        if success:
            logger.info("NeuraReview completed successfully")
        else:
            logger.error("NeuraReview failed")

        return 0 if success else 1
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
