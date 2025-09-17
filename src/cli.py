import argparse
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

    args = parser.parse_args()

    if args.verbose:
        import logging

        logging.getLogger().setLevel(logging.DEBUG)

    try:
        config = Config.from_env()
        reviewer = NeuraReview(config)

        if args.file:
            analysis = reviewer.analyze_single_file(args.repo, args.pr, args.file)
            if analysis is None:
                print("Failed to analyze file")
                return 1
            print(f"Overall: {analysis.overall_comment}")
            print(f"Issues found: {len(analysis.issues)}")
            return 0

        success = reviewer.review_pull_request(
            repo_name=args.repo, pr_number=args.pr, dry_run=args.dry_run
        )
        return 0 if success else 1
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
