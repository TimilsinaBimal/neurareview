"""Diff parsing with correct GitHub position calculation."""

import logging
from typing import List
from unidiff import PatchSet, UnidiffParseError

from .models import FileDiff, DiffHunk, DiffLine, LineType


logger = logging.getLogger(__name__)


class DiffParser:
    """Parse diffs and calculate correct GitHub positions."""

    def parse_file_diff(self, file_diff: FileDiff) -> FileDiff:
        """Parse a file's patch and populate hunks with correct positions."""
        if not file_diff.patch:
            logger.warning(f"No patch content for file: {file_diff.filename}")
            return file_diff

        try:
            # Ensure patch has proper headers for unidiff
            patch_content = self._ensure_patch_headers(
                file_diff.patch, file_diff.filename
            )

            # Parse with unidiff
            patch_set = PatchSet(patch_content.splitlines(keepends=True))

            if not patch_set:
                logger.warning(f"No parseable hunks in patch for: {file_diff.filename}")
                return file_diff

            # Process each hunk
            hunks = []
            for patched_file in patch_set:
                for hunk in patched_file:
                    parsed_hunk = self._parse_hunk(hunk)
                    hunks.append(parsed_hunk)

            file_diff.hunks = hunks
            return file_diff

        except UnidiffParseError as e:
            logger.error(f"Failed to parse patch for {file_diff.filename}: {e}")
            return file_diff
        except Exception as e:
            logger.error(
                f"Unexpected error parsing patch for {file_diff.filename}: {e}"
            )
            return file_diff

    def _ensure_patch_headers(self, patch: str, filename: str) -> str:
        """Ensure patch has proper headers for unidiff parsing."""
        if not patch.startswith("--- "):
            # Add minimal headers if missing
            header = f"--- a/{filename}\n+++ b/{filename}\n"
            return header + patch
        return patch

    def _parse_hunk(self, hunk) -> DiffHunk:
        """Parse a single hunk."""
        lines = []
        old_line_num = hunk.source_start
        new_line_num = hunk.target_start

        for line in hunk:
            line_type = LineType.CONTEXT
            old_line = None
            new_line = None

            if line.is_added:
                line_type = LineType.ADDED
                new_line = new_line_num
                new_line_num += 1
            elif line.is_removed:
                line_type = LineType.REMOVED
                old_line = old_line_num
                old_line_num += 1
            else:  # Context line
                line_type = LineType.CONTEXT
                old_line = old_line_num
                new_line = new_line_num
                old_line_num += 1
                new_line_num += 1

            diff_line = DiffLine(
                type=line_type,
                content=line.value.rstrip("\n"),
                old_line_number=old_line,
                new_line_number=new_line,
            )
            lines.append(diff_line)

        return DiffHunk(
            old_start=hunk.source_start,
            old_count=hunk.source_length,
            new_start=hunk.target_start,
            new_count=hunk.target_length,
            lines=lines,
            header=str(hunk).split("\n")[0],
        )

    def extract_added_lines(self, file_diff: FileDiff) -> List[DiffLine]:
        """Extract all added lines from a file diff."""
        added_lines = []
        for hunk in file_diff.hunks:
            for line in hunk.lines:
                if line.type == LineType.ADDED:
                    added_lines.append(line)
        return added_lines

    def extract_removed_lines(self, file_diff: FileDiff) -> List[DiffLine]:
        """Extract all removed lines from a file diff."""
        removed_lines = []
        for hunk in file_diff.hunks:
            for line in hunk.lines:
                if line.type == LineType.REMOVED:
                    removed_lines.append(line)
        return removed_lines

    def get_file_summary(self, file_diff: FileDiff) -> str:
        """Get a summary of changes in the file."""
        added_count = len(self.extract_added_lines(file_diff))
        removed_count = len(self.extract_removed_lines(file_diff))

        summary = f"File: {file_diff.filename}\n"
        summary += f"Status: {file_diff.status}\n"
        summary += f"Changes: +{added_count} -{removed_count}\n"

        if file_diff.old_filename and file_diff.old_filename != file_diff.filename:
            summary += f"Renamed from: {file_diff.old_filename}\n"

        return summary
