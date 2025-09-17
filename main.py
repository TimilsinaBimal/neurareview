#!/usr/bin/env python3
"""
NeuraReview - AI-powered code review agent
Usage: python main_new.py --repo owner/repo --pr 123 [--dry-run]
"""

import argparse
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.neura_review import NeuraReview
from src.config import Config


def main():
    """Main entry point for NeuraReview."""
    parser = argparse.ArgumentParser(
        description="AI-powered code review agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main_new.py --repo owner/repo --pr 123
  python main_new.py --repo owner/repo --pr 123 --dry-run
  python main_new.py --repo owner/repo --pr 123 --file specific_file.py
        """,
    )

    parser.add_argument(
        "--repo", required=True, help="Repository in format 'owner/repo'"
    )

    parser.add_argument("--pr", type=int, required=True, help="Pull request number")

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Analyze and prepare review but don't post to GitHub",
    )

    parser.add_argument("--file", help="Analyze only a specific file in the PR")

    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )

    args = parser.parse_args()

    # Set up logging level
    if args.verbose:
        import logging

        logging.getLogger().setLevel(logging.DEBUG)

    try:
        # Load configuration from environment
        config = Config.from_env()

        # Initialize NeuraReview
        reviewer = NeuraReview(config)

        if args.file:
            # Analyze single file
            print(f"Analyzing single file: {args.file}")
            analysis = reviewer.analyze_single_file(args.repo, args.pr, args.file)

            if analysis:
                print(f"\nAnalysis for {args.file}:")
                print(f"Overall: {analysis.overall_comment}")
                print(f"Issues found: {len(analysis.issues)}")
                for issue in analysis.issues:
                    print(f"  - {issue.severity.value}: {issue.title}")
            else:
                print("Failed to analyze file")
                return 1
        else:
            # Review entire PR
            print(f"Reviewing PR #{args.pr} in {args.repo}")
            if args.dry_run:
                print("DRY RUN MODE - No comments will be posted")

            success = reviewer.review_pull_request(
                repo_name=args.repo, pr_number=args.pr, dry_run=args.dry_run
            )

            if success:
                print("✅ Review completed successfully!")
                return 0
            else:
                print("❌ Review failed")
                return 1

    except KeyboardInterrupt:
        print("\n⏹️  Review cancelled by user")
        return 1
    except Exception as e:
        print(f"❌ Error: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
